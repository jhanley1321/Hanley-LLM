# llm.py
from dataclasses import dataclass
from typing import Generator, Optional
import time

@dataclass
class LLMResponse:
    """Standardized response wrapper for any LLM backend."""
    status_code: int  # 200=success, 400=client error, 500=server error, etc.
    status_message: str  # "ok", "rate_limited", "model_unavailable", etc.
    backend_latency_ms: float
    token_stream: Optional[Generator] = None
    error_details: Optional[str] = None

class LLM_Model:
    def __init__(self):
        self.model_type = None
        self.model_name = None

    def load_model(self, model_type: str, model: str):
        self.model_type = model_type
        self.model_name = model
        print(f"Loading {model_type} model: {model}")

    def chat_stream(self, message: str) -> LLMResponse:
        """
        Universal method that works with any LLM backend.
        Returns standardized LLMResponse with status info.
        """
        start_time = time.time()
        
        try:
            if self.model_type == "ollama":
                return self._ollama_chat_stream(message, start_time)
            elif self.model_type == "openai":
                return self._openai_chat_stream(message, start_time)
            elif self.model_type == "anthropic":
                return self._anthropic_chat_stream(message, start_time)
            else:
                latency = (time.time() - start_time) * 1000
                return LLMResponse(
                    status_code=501,
                    status_message="unsupported_model_type",
                    backend_latency_ms=latency,
                    error_details=f"Model type '{self.model_type}' not implemented"
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                status_code=500,
                status_message="backend_exception",
                backend_latency_ms=latency,
                error_details=str(e)
            )

    def _ollama_chat_stream(self, message: str, start_time: float) -> LLMResponse:
        """Ollama-specific implementation."""
        try:
            # Your existing Ollama streaming logic here
            def token_generator():
                for i, word in enumerate(["Hello", "world", "from", "Ollama"]):
                    yield f"{word} "
                    if i >= 50:  # Simulate some limit
                        break
            
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                status_code=200,
                status_message="ok",
                backend_latency_ms=latency,
                token_stream=token_generator()
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            # Map Ollama-specific errors to standard codes
            if "connection" in str(e).lower():
                return LLMResponse(
                    status_code=503,
                    status_message="connection_error",
                    backend_latency_ms=latency,
                    error_details=str(e)
                )
            else:
                return LLMResponse(
                    status_code=500,
                    status_message="ollama_error",
                    backend_latency_ms=latency,
                    error_details=str(e)
                )

    def _openai_chat_stream(self, message: str, start_time: float) -> LLMResponse:
        """OpenAI-specific implementation."""
        # TODO: Implement OpenAI streaming with error handling
        # Map OpenAI errors (rate limits, invalid API key, etc.) to standard codes
        pass

    def _anthropic_chat_stream(self, message: str, start_time: float) -> LLMResponse:
        """Anthropic-specific implementation."""
        # TODO: Implement Anthropic streaming with error handling
        pass