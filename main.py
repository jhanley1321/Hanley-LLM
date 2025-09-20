import uvicorn
from dotenv import load_dotenv
from llm import LLM_Model
from fastapi import FastAPI
from chat_api import ChatAPI

load_dotenv()



app = FastAPI()
chat_api = ChatAPI()
app.include_router(chat_api.router)

    

def main():
  
    
    llm = LLM_Model()
    llm.load_model(model_type="ollama", model="llama3.2")



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
    main()

    