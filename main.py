from llm import LLM_Model
from dotenv import load_dotenv
import os

load_dotenv()




def main(agent=False, chatbot=True, vector_db=True):
    llm = LLM_Model()
    # llm.load_model(model_type='openai')
    llm.load_model(model_type='ollama', model="llama3.2") 

    
    if vector_db:
        # Load vector database
        llm.load_chroma_db( # add support for other vector dbs later 
            collection_name="restaurant_reviews",
            persist_directory="./chrome_langchain_db"
        )

        # # Check if the database is empty and load CSV if needed
        # if not os.path.exists("./chrome_langchain_db"):
        #     llm.vector_db.load_csv("data/realistic_restaurant_reviews.csv")

        llm.vector_db.view_data()
        llm.vector_db.load_csv(csv="realistic_restaurant_reviews.csv")

        # llm.vector_db.delete_all_data()
        llm.vector_db.view_data()



    if chatbot:
        if agent:
            llm.load_agent()
            llm.agent_handler.run_agent()
        else:
            llm.run_chatbot()


if __name__ == "__main__":
    main(agent=False, chatbot=True, vector_db=True)

    