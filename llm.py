from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from langchain_community.chat_message_histories import ChatMessageHistory


class LLM_Model:
    def __init__(self, max_memory: int = 5):
        self.model = None
        self.memory = ChatMessageHistory()
        self.model_classes = {
            "openai": ChatOpenAI,
            "ollama": OllamaLLM,
        }
        self.response_attribute = "content"  # Default for models that return objects
        self.max_memory = max_memory
    
    def load_model(self, model_type: str = "openai", **kwargs):
        """Load the requested model (OpenAI or Ollama)"""
        if model_type not in self.model_classes:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        self.model = self.model_classes[model_type](**kwargs)
        if model_type == "ollama":
            # Ollama's wrapper returns just a string
            self.response_attribute = None
        print(f"Model '{model_type}' loaded successfully.")

    def chat(self, user_message: str) -> str:
        """Single‑turn chat — takes a string input, returns a string reply"""
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Convert memory into prompt/history (optional for later)
        history_str = ""
        for msg in self.memory.messages[-self.max_memory:]:
            if isinstance(msg, HumanMessage):
                history_str += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"Assistant: {msg.content}\n"

        prompt = f"{history_str}User: {user_message}\nAssistant:"

        # Call model
        response = self.model.invoke(prompt)

        # Handle response type (object vs string)
        assistant_reply = (
            response if self.response_attribute is None
            else getattr(response, self.response_attribute)
        )

        # Update memory
        self.memory.add_user_message(user_message)
        self.memory.add_ai_message(assistant_reply)

        return assistant_reply



    def chat_stream(self, user_message: str):
        """Stream the LLM response token by token."""
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Build minimal prompt (later we can add memory/context again)
        prompt = f"User: {user_message}\nAssistant:"

        # Call model with streaming enabled
        for chunk in self.model.stream(prompt):
            # Ollama yields strings, OpenAI yields objects
            text_chunk = chunk if self.response_attribute is None else getattr(chunk, self.response_attribute)
            yield text_chunk