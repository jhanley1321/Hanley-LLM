# tests/conftest.py
"""Shared test fixtures and configuration."""

import pytest
import tempfile
import shutil
import os
import logging
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI



@pytest.fixture
def temp_dir():
    """Create temporary directory for test isolation."""
    temp_path = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_path)

    yield temp_path

    # Cleanup
    os.chdir(original_cwd)

    # Ensure logging closes file handles before deleting temp dir
    logging.shutdown()

    try:
        shutil.rmtree(temp_path)
    except PermissionError:
        # On Windows logging may still hold file handles briefly
        pass

@pytest.fixture
def mock_llm():
    """Mock LLM_Model for testing."""
    mock = Mock()
    mock.chat_stream.return_value = iter(["Hello", " ", "world"])
    return mock


@pytest.fixture
def mock_user():
    """Mock authenticated user context."""
    return {"user_id": "test_user", "tenant_id": "test_tenant"}


@pytest.fixture
def test_client():
    """FastAPI test client with mocked dependencies."""
    with patch('chat_api.LLM_Model') as mock_llm_class:
        mock_llm_class.return_value = Mock()
        
        from chat_api import ChatAPI
        chat_api = ChatAPI(local_log=False)
        
        app = FastAPI()
        app.include_router(chat_api.router)
        
        return TestClient(app)