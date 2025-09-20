# chat_api.py
import os # <-- Import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from llm import LLM_Model
from pydantic import BaseModel
from auth import get_current_user
import time, threading
from dotenv import load_dotenv # <-- Import load_dotenv here too (defensive)

# Load environment variables (defensive, main.py also loads)
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
    def __init__(self):
        self.router = APIRouter()
        self.llm = LLM_Model()
        self.llm.load_model(model_type="ollama", model="llama3.2")

        # --- Simplified Config Loading from .env ---
        self.MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
        self.MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "150"))
        self.REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
        # --- End Simplified Config ---

        self.router.post("/chat")(self.chat_endpoint)

    def stream_chat_response(self, message: str):
        if len(message) > self.MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Message too long. Max {self.MAX_INPUT_LENGTH} characters."
            )

        raw_stream = self.llm.chat_stream(message)
        limited_stream = TokenLimiter.limit_tokens(raw_stream, self.MAX_OUTPUT_TOKENS)

        start_time = time.time()
        timed_out = False

        def timeout_trigger():
            nonlocal timed_out
            timed_out = True

        timer = threading.Timer(self.REQUEST_TIMEOUT_SECONDS, timeout_trigger)
        timer.start()

        try:
            for sse_event in SSEFormatter.format_stream(limited_stream):
                if timed_out:
                    yield "data: [ERROR] Request timed out\n\n"
                    yield "data: [DONE]\n\n"
                    break
                yield sse_event
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
            self.stream_chat_response(message),
            media_type="text/event-stream"
        )