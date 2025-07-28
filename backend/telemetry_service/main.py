import os
import psycopg2
from psycopg2.extras import register_uuid
import jwt
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID

load_dotenv()

class TelemetryData(BaseModel):
    device_id: str 
    energy_usage: float

class DeviceCreate(BaseModel):
    name: str
    type: str
    room: str
    power_rating: float

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    power_rating: Optional[float] = None

class ScheduleBlock(BaseModel):
    day_of_week: int
    start_hour: int
    end_hour: int
    power_consumption: float

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_id = cur.fetchone()[0]
        conn.close()
        return user_id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="smart_home_db",
            port="5432"
        )
        register_uuid()
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

@app.post("/devices", status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate, user_id: UUID = Depends(get_current_user_id)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO devices (user_id, name, type, room, power_rating) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (user_id, device.name, device.type, device.room, device.power_rating)
            )
            device_id = cur.fetchone()[0]
            
            # Initialize with zero reading for immediate visibility
            cur.execute(
                """INSERT INTO telemetry (timestamp, device_id, energy_usage)
                   VALUES (NOW(), %s, 0)""",
                (device_id,)
            )
        conn.commit()
        return {"id": str(device_id), "message": "Device created successfully"}
    finally:
        conn.close()

@app.put("/devices/{device_id}")
def update_device(device_id: UUID, device_update: DeviceUpdate, user_id: UUID = Depends(get_current_user_id)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM devices WHERE id = %s AND user_id = %s", (device_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Device not found")
            
            updates = []
            values = []
            if device_update.name:
                updates.append("name = %s")
                values.append(device_update.name)
            if device_update.power_rating:
                updates.append("power_rating = %s")
                values.append(device_update.power_rating)
            
            if updates:
                values.extend([device_id, user_id])
                cur.execute(
                    f"UPDATE devices SET {', '.join(updates)} WHERE id = %s AND user_id = %s",
                    values
                )
        conn.commit()
        return {"message": "Device updated successfully"}
    finally:
        conn.close()

@app.post("/devices/{device_id}/schedule")
def set_device_schedule(device_id: UUID, schedule: List[ScheduleBlock], user_id: UUID = Depends(get_current_user_id)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM devices WHERE id = %s AND user_id = %s", (device_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Device not found")
            
            cur.execute("DELETE FROM device_schedules WHERE device_id = %s", (device_id,))
            
            for block in schedule:
                cur.execute(
                    """INSERT INTO device_schedules (device_id, day_of_week, start_hour, end_hour, power_consumption)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (device_id, block.day_of_week, block.start_hour, block.end_hour, block.power_consumption)
                )
        conn.commit()
        return {"message": "Schedule updated successfully"}
    finally:
        conn.close()

@app.get("/devices/{device_id}/schedule")
def get_device_schedule(device_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM devices WHERE id = %s AND user_id = %s", (device_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Device not found")
            
            cur.execute(
                """SELECT day_of_week, start_hour, end_hour, power_consumption 
                   FROM device_schedules WHERE device_id = %s ORDER BY day_of_week, start_hour""",
                (device_id,)
            )
            schedule = [
                {
                    "day_of_week": row[0],
                    "start_hour": row[1],
                    "end_hour": row[2],
                    "power_consumption": row[3]
                }
                for row in cur.fetchall()
            ]
        return {"schedule": schedule}
    finally:
        conn.close()

@app.delete("/devices/{device_id}")
def delete_device(device_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM devices WHERE id = %s AND user_id = %s", (device_id, user_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Device not found")
        conn.commit()
        return {"message": "Device deleted successfully"}
    finally:
        conn.close()

@app.get("/")
def read_root():
    return {"status": "Telemetry Service is running"}

@app.post("/telemetry", status_code=status.HTTP_201_CREATED)
def record_telemetry(data: TelemetryData):
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