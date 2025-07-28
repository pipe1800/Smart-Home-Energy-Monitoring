import os
import psycopg2
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class TelemetryData(BaseModel):
    device_id: str 
    energy_usage: float

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get database connection"""
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
        return None

@app.get("/")
def read_root():
    return {"status": "Telemetry Service is running"}

@app.post("/telemetry", status_code=status.HTTP_201_CREATED)
def record_telemetry(data: TelemetryData):
    """Record telemetry data"""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the database."
        )
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry (timestamp, device_id, energy_usage)
                VALUES (NOW(), %s, %s)
                """,
                (data.device_id, data.energy_usage)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()
        
    return {"message": "Telemetry data recorded successfully", "data": data}