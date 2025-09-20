from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from llm_tools import LLM_Tools
from llm_agents import LLM_Agents
from chroma_db import ChromaVectorDB







#
class LLM_Model:
    def __init__(self, max_memory=5):
        self.model = None
        self.agent_handler = None
        self.memory = ChatMessageHistory()
        self.vector_db = None  # Add vector database attribute
        self.model_classes = {
            'openai': ChatOpenAI,
            'ollama': OllamaLLM,
        }
        self.response_attribute = "content"  # Default for OpenAI

    def load_model(self, model_type='openai', **kwargs):
        if model_type in self.model_classes:
            self.model = self.model_classes[model_type](**kwargs)
            if model_type == 'ollama':
                self.response_attribute = None  # No attribute for Ollama
            print(f"Model '{model_type}' loaded successfully.")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def load_chroma_db(self, collection_name="default_collection", persist_directory="./chroma_db"):
        """Load the vector database for retrieval"""
        self.vector_db = ChromaVectorDB(
            collection_name=collection_name,
            persist_directory=persist_directory
        )

    def load_agent(self):
        self.agent_handler = LLM_Agents(self.model)
        self.agent_handler.load_agent()

    def run_chatbot(self):
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "quit":
                print('Shutting Down... Thank you!')
                break
            elif user_input.lower() == "toggle agent":
                break

            # Build conversation history as a string
            history_str = ""
            for msg in self.memory.messages:
                if isinstance(msg, HumanMessage):
                    history_str += f"User: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    history_str += f"Assistant: {msg.content}\n"

            # Get relevant context from vector database if available
            context_str = ""
            if self.vector_db:
                retriever = self.vector_db.get_retriever(search_kwargs={"k": 3})
                relevant_docs = retriever.invoke(user_input)
                if relevant_docs:
                    context_str = "\nRelevant information:\n"
                    for doc in relevant_docs:
                        context_str += f"- {doc.page_content}\n"

            # Combine history, context, and current input
            prompt = f"{history_str}{context_str}User: {user_input}\nAssistant:"

            # Get response from the LLM
            response = self.model.invoke(prompt)

            # Extract response based on model type
            assistant_reply = response if self.response_attribute is None else getattr(response, self.response_attribute)

            print("\nAssistant:", assistant_reply)

            # Save the turn to memory
            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(assistant_reply)

    def __getattr__(self, name):
        """Delegate attribute access to agent_handler if it exists"""
        if self.agent_handler and hasattr(self.agent_handler, name):
            return getattr(self.agent_handler, name)
        raise AttributeError(f"'LLM_Model' object has no attribute '{name}'")