import os
import traceback
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase Initialization
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class UserCredentials(BaseModel):
    email: EmailStr
    password: str

app = FastAPI()

@app.get("/auth")
def read_root():
    return {"status": "Auth Service is running"}

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(credentials: UserCredentials):
    """Register new user"""
    try:
        res = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password,
        })
        if res.user is None and res.session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User likely already exists or password is too weak."
            )
        return {"message": "Registration successful, please check your email to verify."}
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/auth/login")
def login_user(credentials: UserCredentials):
    """Authenticate user"""
    try:
        res = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })
        return res.session
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {e}"
        )