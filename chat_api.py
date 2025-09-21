# chat_api.py
import os, time, json, threading, logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from llm import LLM_Model
from pydantic import BaseModel
from auth import get_current_user
from dotenv import load_dotenv

load_dotenv()


class ChatRequest(BaseModel):
    message: str


class TokenLimiter:
    @staticmethod
    def limit_tokens(generator, max_tokens: int):
        count = 0
        for token in generator:
            if token:
                yield token
                count += 1
                if count >= max_tokens:
                    yield "[STOP_SEQUENCE_MAX_TOKENS]"
                    break


class SSEFormatter:
    @staticmethod
    def format_stream(generator):
        try:
            for item in generator:
                yield f"data: {item}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"


class ChatAPI:
    def __init__(self, local_log: bool = True, log_file: str = "chat_api.log"):
        self.router = APIRouter()
        self.llm = LLM_Model()
        self.llm.load_model(model_type="ollama", model="llama3.2")

        # Config values from .env with defaults
        self.MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
        self.MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "150"))
        self.REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

        # Logging setup
        self.local_log = local_log
        if self.local_log:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_path = log_dir / log_file
            logging.basicConfig(
                filename=log_path,
                level=logging.INFO,
                format="%(message)s",
                force=True   # FIX: ensure logging reconfigures each test
            )

        # Register endpoint
        self.router.post("/chat")(self.chat_endpoint)

    def stream_chat_response(self, message: str, user_ctx: dict):
        """Handles chat stream with timeout + logging."""

        if len(message) > self.MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Message too long. Max {self.MAX_INPUT_LENGTH} characters."
            )

        # --- Backend call (Ollama or future LLMs) ---
        backend_start = time.time()
        try:
            raw_stream = self.llm.chat_stream(message)  # existing generator
            backend_status = 200
            backend_message = "ok"
        except Exception as e:
            latency = (time.time() - backend_start) * 1000
            self.log_request(
                user_ctx, len(message), 0, latency,
                "backend_error", backend_status=500, backend_message=str(e)
            )
            raise HTTPException(status_code=502, detail=f"LLM backend error: {str(e)}")

        backend_latency = (time.time() - backend_start) * 1000
        limited_stream = TokenLimiter.limit_tokens(raw_stream, self.MAX_OUTPUT_TOKENS)

        # --- Timeout & streaming ---
        start_time = time.time()
        token_count = 0
        timed_out = False

        def timeout_trigger():
            nonlocal timed_out
            timed_out = True

        timer = threading.Timer(self.REQUEST_TIMEOUT_SECONDS, timeout_trigger)
        timer.start()

        try:
            for sse_event in SSEFormatter.format_stream(limited_stream):
                if timed_out:
                    total_latency = (time.time() - start_time) * 1000 + backend_latency
                    self.log_request(
                        user_ctx, len(message), token_count, total_latency,
                        "timeout", backend_status, backend_message
                    )
                    yield "data: [ERROR] Request timed out\n\n"
                    yield "data: [DONE]\n\n"
                    break

                if not (sse_event.startswith("data: [") and sse_event.endswith("]\n\n")):
                    token_count += 1

                yield sse_event

            if not timed_out:
                total_latency = (time.time() - start_time) * 1000 + backend_latency
                self.log_request(
                    user_ctx, len(message), token_count, total_latency,
                    "ok", backend_status, backend_message
                )

        except Exception as e:
            total_latency = (time.time() - start_time) * 1000 + backend_latency
            self.log_request(
                user_ctx, len(message), token_count, total_latency,
                "error", backend_status, "stream_error"
            )
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            timer.cancel()

    async def chat_endpoint(
        self, 
        payload: ChatRequest, 
        current_user: dict = Depends(get_current_user)
    ):
        message = payload.message
        if not message.strip():
            raise HTTPException(status_code=400, detail="Missing message")

        return StreamingResponse(
            self.stream_chat_response(message, current_user),
            media_type="text/event-stream"
        )

    def log_request(self, user_ctx, input_length, output_tokens, latency_ms,
                    status, backend_status=None, backend_message=None):
        """Structured logging for each request."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_ctx.get("user_id"),
            "tenant_id": user_ctx.get("tenant_id"),
            "input_length": input_length,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 2),
            "status": status,
            "backend_status": backend_status,
            "backend_message": backend_message
        }

        # Always stdout
        print(json.dumps(log_data))

        # Also write to file if enabled
        if self.local_log:
            logging.info(json.dumps(log_data))