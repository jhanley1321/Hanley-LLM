# auth.py
import os
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Make sure environment is loaded
load_dotenv()

# Read from env
SECRET_TOKEN = os.getenv("HANLEY_LLM_SECRET_TOKEN")

if not SECRET_TOKEN:
    raise RuntimeError("Environment variable HANLEY_LLM_SECRET_TOKEN not set!")

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validate incoming Bearer token.
    """
    print(f"DEBUG: Expected token from .env: {SECRET_TOKEN}")
    print(f"DEBUG: Received token in request: {credentials.credentials}")
    
    if credentials.credentials == SECRET_TOKEN:
        return {"user_id": "demo-user", "tenant_id": "demo-tenant"}
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )