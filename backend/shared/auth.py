import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "user_id": user_id}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """Extract user ID from JWT token"""
    token_data = decode_token(token)
    return token_data["user_id"]

def get_current_user_email(token: str = Depends(oauth2_scheme)):
    """Extract user email from JWT token"""
    token_data = decode_token(token)
    return token_data["email"]
