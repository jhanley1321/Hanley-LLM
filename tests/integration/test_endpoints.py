# tests/integration/test_endpoints.py
"""Integration tests for API endpoints."""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from chat_api import ChatAPI


class TestChatEndpoint:
    """Test /chat endpoint integration."""
    
    def setup_method(self, temp_dir):
        """Set up test client with mocked dependencies."""
        self.mock_llm = Mock()
        
        with patch('chat_api.LLM_Model') as mock_llm_class:
            mock_llm_class.return_value = self.mock_llm
            self.chat_api = ChatAPI(local_log=False)
        
        self.app = FastAPI()
        self.app.include_router(self.chat_api.router)
        self.client = TestClient(self.app)
        
        self.mock_user = {"user_id": "test_user", "tenant_id": "test_tenant"}
    
    def test_missing_authentication(self):
        """Should return 403 when no auth header provided."""
        response = self.client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 403
    
    @patch('chat_api.get_current_user')
    def test_empty_message_validation(self, mock_auth):
        """Should return 400 for empty messages."""
        mock_auth.return_value = self.mock_user
        
        response = self.client.post("/chat", json={"message": ""})
        assert response.status_code == 400
        assert "Missing message" in response.json()["detail"]
    
    @patch('chat_api.get_current_user')
    def test_message_length_validation(self, mock_auth):
        """Should return 413 for messages exceeding length limit."""
        mock_auth.return_value = self.mock_user
        
        # Create message longer than default limit (2000 chars)
        long_message = "x" * 2001
        response = self.client.post("/chat", json={"message": long_message})
        
        assert response.status_code == 413
        assert "Message too long" in response.json()["detail"]
    
    @patch('chat_api.get_current_user')
    def test_successful_streaming(self, mock_auth):
        """Should return streaming response for valid request."""
        mock_auth.return_value = self.mock_user
        
        # Mock LLM response
        def mock_stream():
            yield "Hello"
            yield " "
            yield "world"
        
        self.mock_llm.chat_stream.return_value = mock_stream()
        
        with patch('builtins.print'):  # Suppress log output
            response = self.client.post("/chat", json={"message": "Hello"})
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify SSE format in response
        content = response.text
        assert "data: Hello\n\n" in content
        assert "data:  \n\n" in content
        assert "data: world\n\n" in content
        assert "data: [DONE]\n\n" in content
    
    @patch('chat_api.get_current_user')
    def test_backend_error_handling(self, mock_auth):
        """Should return 502 when LLM backend fails."""
        mock_auth.return_value = self.mock_user
        
        # Mock LLM to raise exception
        self.mock_llm.chat_stream.side_effect = ConnectionError("Ollama unavailable")
        
        with patch('builtins.print'):  # Suppress log output
            response = self.client.post("/chat", json={"message": "Hello"})
        
        assert response.status_code == 502
        assert "LLM backend error" in response.json()["detail"]
    
    @patch('chat_api.get_current_user')
    def test_request_timeout(self, mock_auth):
        """Should handle request timeout gracefully."""
        mock_auth.return_value = self.mock_user
        
        # Create slow generator to trigger timeout
        def slow_stream():
            time.sleep(0.1)
            yield "Hello"
            time.sleep(0.1)  # This should trigger timeout
            yield "world"
        
        self.mock_llm.chat_stream.return_value = slow_stream()
        
        # Set very short timeout for testing
        self.chat_api.REQUEST_TIMEOUT_SECONDS = 0.05
        
        with patch('builtins.print'):  # Suppress log output
            response = self.client.post("/chat", json={"message": "Hello"})
        
        assert response.status_code == 200
        content = response.text
        assert "data: [ERROR] Request timed out\n\n" in content
        assert "data: [DONE]\n\n" in content