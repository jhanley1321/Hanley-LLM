import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from llm import LLM_Model

from api.chat_api import ChatAPI

load_dotenv()



app = FastAPI()
chat_api = ChatAPI(local_log=True)
app.include_router(chat_api.router)

    

def main():
  
    
    llm = LLM_Model()
    llm.load_model(model_type="ollama", model="llama3.2")
    llm.chat_stream()



if __name__ == "__main__":
    
    uvicorn.run("main:app", reload=True)
    main()

    