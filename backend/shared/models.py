from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str
    room: str
    power_rating: float = Field(..., gt=0, le=50)  # Max 50kW

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    power_rating: Optional[float] = Field(None, gt=0, le=50)

def success_response(data=None, message="Success"):
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error_response(message, code=400):
    return {
        "status": "error",
        "message": message,
        "code": code
    }
