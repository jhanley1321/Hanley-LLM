# tests/unit/test_chat_api.py
"""Unit tests for ChatAPI class and configuration."""

import pytest
import os
import json
from unittest.mock import Mock, patch
from pathlib import Path
from chat_api import ChatAPI


class TestChatAPIConfiguration:
    """Test ChatAPI initialization and configuration."""
    
    def test_default_config(self):
        """Should use default values when no env vars set."""
        # FIX: Clear all env vars so defaults apply
        with patch.dict(os.environ, {}, clear=True):
            with patch('chat_api.LLM_Model') as mock_llm_class:
                mock_llm_class.return_value = Mock()

                api = ChatAPI(local_log=False)

                assert api.MAX_INPUT_LENGTH == 2000
                assert api.MAX_OUTPUT_TOKENS == 150
                assert api.REQUEST_TIMEOUT_SECONDS == 60
    
    def test_env_var_config(self):
        """Should load config from environment variables."""
        env_vars = {
            'MAX_INPUT_LENGTH': '3000',
            'MAX_OUTPUT_TOKENS': '200',
            'REQUEST_TIMEOUT_SECONDS': '90'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('chat_api.LLM_Model') as mock_llm_class:
                mock_llm_class.return_value = Mock()
                
                api = ChatAPI(local_log=False)
                
                assert api.MAX_INPUT_LENGTH == 3000
                assert api.MAX_OUTPUT_TOKENS == 200
                assert api.REQUEST_TIMEOUT_SECONDS == 90
    
    def test_logging_setup(self, temp_dir):
        """Should create logs directory when local_log enabled."""
        with patch('chat_api.LLM_Model') as mock_llm_class:
            mock_llm_class.return_value = Mock()
            
            api = ChatAPI(local_log=True, log_file="test.log")
            
            assert Path("logs").exists()
            assert api.local_log == True


class TestChatAPILogging:
    """Test structured logging functionality."""
    
    def test_log_structure(self, temp_dir):
        """Should create properly structured JSON logs."""
        with patch('chat_api.LLM_Model') as mock_llm_class:
            mock_llm_class.return_value = Mock()
            api = ChatAPI(local_log=False)
        
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        with patch('builtins.print') as mock_print:
            api.log_request(
                user_ctx=user_ctx,
                input_length=100,
                output_tokens=50,
                latency_ms=1500.5,
                status="ok",
                backend_status=200,
                backend_message="success"
            )
        
        # Verify JSON structure
        mock_print.assert_called_once()
        log_json = json.loads(mock_print.call_args[0][0])
        
        assert log_json["user_id"] == "test_user"
        assert log_json["tenant_id"] == "test_tenant"
        assert log_json["input_length"] == 100
        assert log_json["output_tokens"] == 50
        assert log_json["latency_ms"] == 1500.5
        assert log_json["status"] == "ok"
        assert log_json["backend_status"] == 200
        assert log_json["backend_message"] == "success"
        assert "timestamp" in log_json
    
    def test_file_logging(self, temp_dir):
        """Should write logs to file when enabled."""
        # FIX: Reset logging system so basicConfig runs
        import logging
        logging.shutdown()

        with patch('chat_api.LLM_Model') as mock_llm_class:
            mock_llm_class.return_value = Mock()
            api = ChatAPI(local_log=True, log_file="test.log")

        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}

        api.log_request(
            user_ctx=user_ctx,
            input_length=100,
            output_tokens=50,
            latency_ms=1500.5,
            status="ok"
        )

        # Verify file creation and content
        log_file = Path("logs/test.log")
        assert log_file.exists()

        with open(log_file, 'r') as f:
            log_content = f.read().strip()

        log_json = json.loads(log_content)
        assert log_json["user_id"] == "test_user"
        assert log_json["status"] == "ok"