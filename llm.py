# llm.py
from dataclasses import dataclass
from typing import Generator
import time

@dataclass
class LLMResponseMeta:
    """Meta information for logging, without breaking streaming."""
    status_code: int
    status_message: str
    backend_latency_ms: float
    error_details: str = ""

class LLM_Model:
    def __init__(self):
        self.model_type = None
        self.model_name = None

    def load_model(self, model_type: str, model: str):
        self.model_type = model_type
        self.model_name = model
        print(f"Loading {model_type} model: {model}")

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """
        Streaming interface expected by chat_api.py:
        Must yield strings (tokens/chunks).
        Logs metadata separately.
        """
        start_time = time.time()
        try:
            if self.model_type == "ollama":
                yield from self._ollama_chat_stream(message)
                latency = (time.time() - start_time) * 1000
                print(LLMResponseMeta(200, "ok", latency))
            elif self.model_type == "openai":
                yield from self._openai_chat_stream(message)
            elif self.model_type == "anthropic":
                yield from self._anthropic_chat_stream(message)
            else:
                yield f"[ERROR] Unsupported model type: {self.model_type}"
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            print(LLMResponseMeta(500, "backend_exception", latency, str(e)))
            yield f"[ERROR] {str(e)}"

    def _ollama_chat_stream(self, message: str) -> Generator[str, None, None]:
        """Ollama-specific streaming implementation."""
        import ollama
        stream = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": message}],
            stream=True
        )
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    def _openai_chat_stream(self, message: str) -> Generator[str, None, None]:
        """Placeholder OpenAI implementation."""
        # TODO: real OpenAI streaming here
        yield "[OpenAI streaming not implemented yet]"

    def _anthropic_chat_stream(self, message: str) -> Generator[str, None, None]:
        """Placeholder Anthropic implementation."""
        # TODO: real Anthropic streaming here
        yield "[Anthropic streaming not implemented yet]"