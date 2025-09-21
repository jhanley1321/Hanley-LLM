# tests/unit/test_utils.py
"""Unit tests for utility classes (TokenLimiter, SSEFormatter)."""

import pytest
from chat_api import TokenLimiter, SSEFormatter


class TestTokenLimiter:
    """Test token limiting functionality."""
    
    def test_tokens_under_limit(self):
        """Should pass through all tokens when under limit."""
        def token_gen():
            for i in range(3):
                yield f"token_{i}"
        
        result = list(TokenLimiter.limit_tokens(token_gen(), max_tokens=5))
        assert result == ["token_0", "token_1", "token_2"]
    
    def test_tokens_at_limit(self):
        """Should cut off at exact limit and add stop sequence."""
        def token_gen():
            for i in range(10):
                yield f"token_{i}"
        
        result = list(TokenLimiter.limit_tokens(token_gen(), max_tokens=3))
        assert len(result) == 4  # 3 tokens + stop sequence
        assert result[-1] == "[STOP_SEQUENCE_MAX_TOKENS]"
    
    def test_empty_tokens_ignored(self):
        """Should skip empty/None tokens but not count toward limit."""
        def mixed_gen():
            yield "token_1"
            yield ""  # empty
            yield None  # None
            yield "token_2"
        
        result = list(TokenLimiter.limit_tokens(mixed_gen(), max_tokens=5))
        assert result == ["token_1", "token_2"]
    
    def test_empty_generator(self):
        """Should handle empty generator gracefully."""
        def empty_gen():
            return
            yield  # unreachable
        
        result = list(TokenLimiter.limit_tokens(empty_gen(), max_tokens=5))
        assert result == []


class TestSSEFormatter:
    """Test Server-Sent Events formatting."""
    
    def test_successful_formatting(self):
        """Should format tokens as SSE with DONE marker."""
        def token_gen():
            yield "Hello"
            yield "World"
        
        result = list(SSEFormatter.format_stream(token_gen()))
        expected = [
            "data: Hello\n\n",
            "data: World\n\n",
            "data: [DONE]\n\n"
        ]
        assert result == expected
    
    def test_exception_handling(self):
        """Should catch exceptions and format as ERROR."""
        def failing_gen():
            yield "Hello"
            raise ValueError("Test error")
        
        result = list(SSEFormatter.format_stream(failing_gen()))
        assert len(result) == 3
        assert result[0] == "data: Hello\n\n"
        assert "data: [ERROR] Test error\n\n" in result[1]
        assert result[2] == "data: [DONE]\n\n"
    
    def test_empty_stream(self):
        """Should handle empty stream with just DONE marker."""
        def empty_gen():
            return
            yield  # unreachable
        
        result = list(SSEFormatter.format_stream(empty_gen()))
        assert result == ["data: [DONE]\n\n"]