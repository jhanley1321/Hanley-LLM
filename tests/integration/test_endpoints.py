# tests/integration/test_endpoints.py
"""Integration tests for API endpoints."""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from chat_api import ChatAPI


class TestChatEndpoint:
    """Test /chat endpoint functionality."""
    
    def setup_method(self, temp_dir):
        """Set up test client with mocked dependencies."""
        self.mock_llm = Mock()

        with patch('chat_api.LLM_Model') as mock_llm_class:
            mock_llm_class.return_value = self.mock_llm
            self.chat_api = ChatAPI(local_log=False)

        self.app = FastAPI()
        self.app.include_router(self.chat_api.router)

        # Dependency override for authentication
        self.mock_user = {"user_id": "test_user", "tenant_id": "test_tenant"}
        from auth import get_current_user
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_user

        self.client = TestClient(self.app)

    def test_missing_authentication(self):
        """Should return 403 when no auth provided."""
        from auth import get_current_user
        del self.app.dependency_overrides[get_current_user]
        
        response = self.client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 403

    def test_empty_message_validation(self):
        """Should return 400 for empty messages."""
        response = self.client.post("/chat", json={"message": ""})
        assert response.status_code == 400

    def test_message_length_validation(self):
        """Should return 413 for messages exceeding length limit."""
        long_message = "x" * 1001  # exceed limit of 1000
        response = self.client.post("/chat", json={"message": long_message})

        assert response.status_code == 413
        assert response.json()["detail"] == "Message too long. Max 1000 characters."

    def test_successful_streaming(self):
        """Should return streaming response for valid request."""
        def mock_stream():
            yield "Hello"
            yield " "
            yield "world"

        self.mock_llm.chat_stream.return_value = mock_stream()

        with patch('builtins.print'):
            response = self.client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        content = response.text
        assert "data: Hello\n\n" in content
        assert "data:  \n\n" in content
        assert "data: world\n\n" in content
        assert "data: [DONE]\n\n" in content

    def test_backend_error_handling(self):
        """Should return 502 when LLM backend fails."""
        self.mock_llm.chat_stream.side_effect = ConnectionError("Ollama unavailable")

        with patch('builtins.print'):
            response = self.client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 502
        assert response.json()["detail"] == "LLM backend error: Ollama unavailable"

    def test_request_timeout(self):
        """Should handle request timeout gracefully."""
        def slow_stream():
            time.sleep(0.1)
            yield "Hello"
            time.sleep(0.1)
            yield "world"

        self.mock_llm.chat_stream.return_value = slow_stream()
        self.chat_api.REQUEST_TIMEOUT_SECONDS = 0.05

        with patch('builtins.print'):
            response = self.client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 200
        content = response.text
        assert "[ERROR] Request timed out" in content