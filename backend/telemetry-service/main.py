import os
from psycopg2.extras import register_uuid
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID

from shared.auth import get_current_user_id
from shared.database import db_pool
from shared.models import DeviceCreate, DeviceUpdate, success_response
from shared.utils import setup_cors, setup_exception_handlers, setup_logging
from shared.rate_limiting import device_rate_limiter

load_dotenv()

# Register UUID adapter for psycopg2
register_uuid()

# Setup logging
logger = setup_logging("telemetry-service")

class TelemetryData(BaseModel):
    device_id: str 
    energy_usage: float

class ScheduleBlock(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=0, le=23)
    power_consumption: float = Field(..., gt=0)

app = FastAPI(title="Telemetry Service", version="1.0.0")

# Setup middleware and exception handlers
setup_cors(app)
setup_exception_handlers(app)

@app.post("/devices", status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate, user_id: UUID = Depends(get_current_user_id)):
    # Apply rate limiting
    device_rate_limiter.check_rate_limit(str(user_id))
    
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO devices (user_id, name, type, room, power_rating) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (user_id, device.name, device.type, device.room, device.power_rating)
            )
            device_id = cur.fetchone()[0]
            
            # Add initial telemetry entry
            cur.execute(
                """INSERT INTO telemetry (timestamp, device_id, energy_usage)
                   VALUES (NOW(), %s, 0)""",
                (device_id,)
            )
    
    logger.info(f"Device created successfully: {device_id} for user {user_id}")
    return success_response(
        data={"id": str(device_id)},
        message="Device created successfully"
    )

@app.put("/devices/{device_id}")
def update_device(device_id: UUID, device_update: DeviceUpdate, user_id: UUID = Depends(get_current_user_id)):
    # Apply rate limiting
    device_rate_limiter.check_rate_limit(str(user_id))
    
    with db_pool.get_connection() as conn:
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
    
    logger.info(f"Device updated successfully: {device_id}")
    return success_response(message="Device updated successfully")

@app.post("/devices/{device_id}/schedule")
def set_device_schedule(device_id: UUID, schedule: List[ScheduleBlock], user_id: UUID = Depends(get_current_user_id)):
    # Apply rate limiting
    device_rate_limiter.check_rate_limit(str(user_id))
    
    with db_pool.get_connection() as conn:
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
    
    logger.info(f"Schedule updated for device: {device_id}")
    return success_response(message="Schedule updated successfully")

@app.get("/devices/{device_id}/schedule")
def get_device_schedule(device_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    with db_pool.get_connection() as conn:
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
    
    return success_response(data={"schedule": schedule})

@app.delete("/devices/{device_id}")
def delete_device(device_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    # Apply rate limiting
    device_rate_limiter.check_rate_limit(str(user_id))
    
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM devices WHERE id = %s AND user_id = %s", (device_id, user_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Device not found")
    
    logger.info(f"Device deleted successfully: {device_id}")
    return success_response(message="Device deleted successfully")

@app.get("/")
def read_root():
    return {"status": "Telemetry Service is running"}

@app.post("/telemetry", status_code=status.HTTP_201_CREATED)
def record_telemetry(data: TelemetryData):
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry (timestamp, device_id, energy_usage)
                VALUES (NOW(), %s, %s)
                """,
                (data.device_id, data.energy_usage)
            )
    
    return success_response(
        data=data.dict(),
        message="Telemetry data recorded successfully"
    )