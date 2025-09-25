from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from llm_tools import LLM_Tools


class LLM_Agents:
    def __init__(self, model):
        self.model = model
        self.tools = []
        self.agent_executor = None

    def load_agent(self):
        self.tools = [LLM_Tools.calculator, LLM_Tools.say_hello]
        self.agent_executor = create_react_agent(self.model, self.tools)
        print("Welcome! I'm your friendly neighborhood LLM, how can I help you today?")

    def run_agent(self):
        while True:
            user_input = input("\nYou: ").strip()
            if user_input == "quit":
                print('Shutting Down... Thank you!')
                break

            print("\nAssistant: ", end="")
            for chunk in self.agent_executor.stream(
                {"messages": [HumanMessage(content=user_input)]}
            ):
                if "agent" in chunk and "messages" in chunk["agent"]:
                    for message in chunk["agent"]["messages"]:
                        print(message.content, end="")
            print()

