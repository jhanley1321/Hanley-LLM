from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool



class LLM_Tools():

    @staticmethod
    @tool
    def calculator(a: float, b: float) -> str:
        """Useful for performing basic arithmetic calculations with numbers"""
        print("Tool has been called.")
        return f"The sum of {a} and {b} is {a + b}"

    @staticmethod
    @tool
    def say_hello(name: str) -> str:
        """Useful for greeting a user"""
        print("Tool has been called.")
        return f"Hello {name}, How are you today?"