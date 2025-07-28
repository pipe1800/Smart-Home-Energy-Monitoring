import os
import bcrypt
import jwt
import psycopg2
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    email: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="smart_home_db",
            port="5432"
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to the database.")

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

def create_default_devices(user_id, conn):
    import random
    from datetime import datetime, timedelta
    
    default_devices = [
        ("Living Room AC", "appliance", "living_room", 3.5),
        ("Kitchen Refrigerator", "appliance", "kitchen", 0.5),
        ("Master Bedroom Light", "light", "bedroom", 0.06),
        ("Smart Thermostat", "thermostat", "living_room", 2.0),
        ("Home Office Outlet", "outlet", "office", 0.3),
        ("Washing Machine", "appliance", "laundry", 2.0),
    ]
    
    default_schedules = {
        "Living Room AC": [(1,18,22,3.5), (2,18,22,3.5), (3,18,22,3.5), (4,18,22,3.5), (5,18,22,3.5), (6,12,23,3.5), (0,12,23,3.5)],
        "Washing Machine": [(2,10,12,2.0), (5,10,12,2.0)],
        "Home Office Outlet": [(1,9,17,0.3), (2,9,17,0.3), (3,9,17,0.3), (4,9,17,0.3), (5,9,17,0.3)],
        "Kitchen Refrigerator": [(d,0,23,0.5) for d in range(7)],
        "Master Bedroom Light": [(d,20,23,0.06) for d in range(7)],
        "Smart Thermostat": [(d,6,9,2.0) for d in range(7)] + [(d,17,22,2.0) for d in range(7)]
    }
    
    with conn.cursor() as cur:
        for name, device_type, room, power_rating in default_devices:
            cur.execute(
                """INSERT INTO devices (user_id, name, type, room, power_rating) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (user_id, name, device_type, room, power_rating)
            )
            device_id = cur.fetchone()[0]
            
            if name in default_schedules:
                for day, start, end, power in default_schedules[name]:
                    cur.execute(
                        """INSERT INTO device_schedules (device_id, day_of_week, start_hour, end_hour, power_consumption)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (device_id, day, start, end, power)
                    )
            
            now = datetime.now()
            for days_ago in range(7):
                timestamp = now - timedelta(days=days_ago)
                day_of_week = (timestamp.weekday() + 1) % 7
                
                if name in default_schedules:
                    day_schedule = [s for s in default_schedules[name] if s[0] == day_of_week]
                    
                    for hour in range(24):
                        timestamp_hour = timestamp.replace(hour=hour, minute=0, second=0)
                        
                        usage = 0
                        for _, start, end, power in day_schedule:
                            if start <= hour < end:
                                usage = power * random.uniform(0.9, 1.1)
                                break
                        
                        if usage > 0:
                            cur.execute(
                                """INSERT INTO telemetry (timestamp, device_id, energy_usage)
                                   VALUES (%s, %s, %s)""",
                                (timestamp_hour, device_id, usage)
                            )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/auth")
def read_root():
    return {"status": "Auth Service is running"}

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    conn = get_db_connection()
    device_count = 0
    user_id = None
    
    try:
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
            
        create_default_devices(user_id, conn)
        conn.commit()
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM devices WHERE user_id = %s", (user_id,))
            device_count = cur.fetchone()[0]
            
        return {"message": "User registered successfully", "user_id": str(user_id), "devices_created": device_count}
            
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
    finally:
        conn.close()

@app.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
            db_user = cur.fetchone()
    finally:
        conn.close()

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