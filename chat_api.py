# chat_api.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from llm import LLM_Model
from pydantic import BaseModel


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
    def __init__(self):
        self.router = APIRouter()
        self.llm = LLM_Model()
        self.llm.load_model(model_type="ollama", model="llama3.2")

        # Configuration
        self.MAX_INPUT_LENGTH = 2000
        self.MAX_OUTPUT_TOKENS = 150

        # Register endpoint
        self.router.post("/chat")(self.chat_endpoint)

    def stream_chat_response(self, message: str):
        """Main streaming logic - NOTE: This is sync, not async."""
        
        # Input validation
        if len(message) > self.MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Message too long. Max {self.MAX_INPUT_LENGTH} characters."
            )

        try:
            # 1. Get raw token stream from model (sync)
            raw_stream = self.llm.chat_stream(message)
            
            # 2. Apply token limiting
            limited_stream = TokenLimiter.limit_tokens(raw_stream, self.MAX_OUTPUT_TOKENS)
            
            # 3. Format as SSE and yield
            for sse_event in SSEFormatter.format_stream(limited_stream):
                yield sse_event
                
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    async def chat_endpoint(self, payload: ChatRequest):
        """Main endpoint handler."""
        if not payload.message.strip():
            raise HTTPException(status_code=400, detail="Missing message")
        
        return StreamingResponse(
            self.stream_chat_response(payload.message),
            media_type="text/event-stream"
        )