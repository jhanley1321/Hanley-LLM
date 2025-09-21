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
    """Utility class to limit token output from any generator."""
    
    @staticmethod
    def limit_tokens(generator, max_tokens: int):
        """Wrap any token generator with a max token limit."""
        count = 0
        for token in generator:
            if token:  # Skip empty tokens
                yield token
                count += 1
                if count >= max_tokens:
                    yield "[STOP_SEQUENCE_MAX_TOKENS]"
                    break


class SSEFormatter:
    """Utility class to format messages as Server-Sent Events."""
    
    @staticmethod
    def format_stream(generator):
        """Wrap a generator and yield SSE-formatted messages."""
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

        # Load configuration from environment variables with defaults
        self.MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
        self.MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "150"))
        self.REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

        # Set up local file logging
        self.local_log = local_log
        if self.local_log:
            # Ensure logs folder exists
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            log_path = log_dir / log_file
            logging.basicConfig(
                filename=log_path,
                level=logging.INFO,
                format="%(message)s"   # Store raw JSON only
            )

        # Register endpoint
        self.router.post("/chat")(self.chat_endpoint)

    def stream_chat_response(self, message: str, user_ctx: dict):
        """Main streaming logic with safety limits and timeout."""
        
        # Input validation
        if len(message) > self.MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Message too long. Max {self.MAX_INPUT_LENGTH} characters."
            )

        # Get token stream from model
        raw_stream = self.llm.chat_stream(message)
        limited_stream = TokenLimiter.limit_tokens(raw_stream, self.MAX_OUTPUT_TOKENS)

        # Set up timeout tracking
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
                    status = "timeout"
                    latency = (time.time() - start_time) * 1000
                    self.log_request(user_ctx, len(message), token_count, latency, status)
                    yield "data: [ERROR] Request timed out\n\n"
                    yield "data: [DONE]\n\n"
                    break

                # Count only "real" tokens (not control messages)
                if not (sse_event.startswith("data: [") and sse_event.endswith("]\n\n")):
                    token_count += 1

                yield sse_event

            # Log successful completion
            if not timed_out:
                latency = (time.time() - start_time) * 1000
                self.log_request(user_ctx, len(message), token_count, latency, "ok")

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.log_request(user_ctx, len(message), token_count, latency, "error")
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            timer.cancel()  # Clean up timer

    async def chat_endpoint(
        self, 
        payload: ChatRequest, 
        current_user: dict = Depends(get_current_user)
    ):
        """Main endpoint handler with authentication."""
        message = payload.message
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Missing message")
        
        return StreamingResponse(
            self.stream_chat_response(message, current_user),
            media_type="text/event-stream"
        )

    def log_request(self, user_ctx, input_length, output_tokens, latency_ms, status):
        """Log structured request data to stdout and optionally to file."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_ctx.get("user_id"),
            "tenant_id": user_ctx.get("tenant_id"),
            "input_length": input_length,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 2),
            "status": status
        }

        # Always print to stdout (for cloud/docker log collection)
        print(json.dumps(log_data))

        # Optionally also log to file
        if self.local_log:
            logging.info(json.dumps(log_data))