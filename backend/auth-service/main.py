import os
import bcrypt
import jwt
import httpx
import uvicorn
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

from shared.database import db_pool
from shared.models import success_response, UserCreate
from shared.utils import setup_cors, setup_exception_handlers, setup_logging
from shared.rate_limiting import auth_rate_limiter

load_dotenv()

# Setup logging
logger = setup_logging("auth-service")

# Environment variables validation
required_env_vars = ["JWT_SECRET", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuration
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'db')}/{os.getenv('POSTGRES_DB')}"
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://device_service:8003")

class TokenData(BaseModel):
    email: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_byte_enc)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def create_user_defaults(user_id: str) -> int:
    """Call device service to create default devices for new user"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DEVICE_SERVICE_URL}/devices/create-defaults",
                json={"user_id": str(user_id)},
                headers={"X-Internal-Request": "true"}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", {}).get("devices_created", 0)
        except httpx.RequestError as e:
            print(f"Error communicating with device service: {e}")
            return 0
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 0

app = FastAPI(title="Auth Service", version="1.0.0")

# Setup middleware and exception handlers
setup_cors(app)
setup_exception_handlers(app)

@app.get("/auth")
def read_root():
    return {"status": "Auth Service is running"}

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    # Apply rate limiting to registration attempts
    auth_rate_limiter.check_rate_limit(user.email)
    
    device_count = 0
    user_id = None
    
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
            existing_user = cur.fetchone()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered."
                )
        
        hashed_pw = hash_password(user.password)
        
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (user.email, hashed_pw)
            )
            user_id = cur.fetchone()[0]
    
    # Request device service to initialize user defaults
    device_count = await create_user_defaults(user_id)
    
    return success_response(
        data={"user_id": str(user_id), "devices_created": device_count},
        message="User registered successfully"
    )


@app.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    
    # Apply rate limiting to login attempts
    auth_rate_limiter.check_rate_limit(email)
    
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
            db_user = cur.fetchone()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    user_id, user_email, hashed_password = db_user

    if not verify_password(password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user_email, "user_id": str(user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)