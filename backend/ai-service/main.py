import os
import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Literal
from datetime import datetime, timedelta

from shared.auth import get_current_user_email
from shared.database import db_pool
from shared.utils import setup_cors, setup_exception_handlers, setup_logging
from shared.rate_limiting import ai_rate_limiter

load_dotenv()

logger = setup_logging("ai-service")

# Check if API key is loaded
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY not found in environment variables")

class QueryRequest(BaseModel):
    question: str

app = FastAPI(title="AI Service", version="1.0.0")
setup_cors(app)
setup_exception_handlers(app)

def get_user_data(user_email):
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (user_email,))
            user_id = cur.fetchone()[0]
            
            cur.execute("""
                SELECT d.name, d.type, d.room, 
                       COALESCE(t.energy_usage, 0) as current_usage,
                       COALESCE(ds.schedule_info, '[]') as schedules
                FROM devices d
                LEFT JOIN LATERAL (
                    SELECT energy_usage 
                    FROM telemetry 
                    WHERE device_id = d.id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ) t ON true
                LEFT JOIN LATERAL (
                    SELECT json_agg(json_build_object(
                        'day', day_of_week,
                        'start', start_hour,
                        'end', end_hour,
                        'power', power_consumption
                    )) as schedule_info
                    FROM device_schedules
                    WHERE device_id = d.id
                ) ds ON true
                WHERE d.user_id = %s
                ORDER BY d.room, d.name
            """, (user_id,))
            devices = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN t.timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN t.energy_usage ELSE 0 END), 0) as today_kwh,
                    COALESCE(SUM(CASE WHEN t.timestamp >= DATE_TRUNC('week', CURRENT_DATE) THEN t.energy_usage ELSE 0 END), 0) as week_kwh,
                    COALESCE(SUM(CASE WHEN t.timestamp >= DATE_TRUNC('month', CURRENT_DATE) THEN t.energy_usage ELSE 0 END), 0) as month_kwh
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = %s
            """, (user_id,))
            usage_totals = cur.fetchone()
            
            cur.execute("""
                SELECT 
                    DATE_TRUNC('hour', t.timestamp) as hour,
                    SUM(t.energy_usage) as usage
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = %s
                AND t.timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour
            """, (user_id,))
            recent_usage = cur.fetchall()
            
            return {
                "devices": [
                    {
                        "name": d[0],
                        "type": d[1],
                        "room": d[2],
                        "current_usage_kw": float(d[3]),
                        "schedules": d[4]
                    } for d in devices
                ],
                "usage_summary": {
                    "today_kwh": float(usage_totals[0]),
                    "week_kwh": float(usage_totals[1]),
                    "month_kwh": float(usage_totals[2]),
                    "current_total_kw": sum(float(d[3]) for d in devices),
                    "active_devices": sum(1 for d in devices if d[3] > 0),
                    "total_devices": len(devices)
                },
                "recent_24h": [
                    {
                        "time": h[0].isoformat(),
                        "usage_kw": float(h[1])
                    } for h in recent_usage
                ],
                "electricity_rate_per_kwh": 0.12
            }

@app.get("/ai")
def read_root():
    return {"status": "AI Service is running", "api_key_configured": bool(OPENROUTER_API_KEY)}

@app.post("/ai/query")
async def handle_query(query: QueryRequest, current_user_email: str = Depends(get_current_user_email)):
    ai_rate_limiter.check_rate_limit(current_user_email)
    
    logger.info(f"User query from {current_user_email}: {query.question}")
    
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not configured")
        return {
            "summary": "Wat - Your Energy Assistant",
            "content": "I'm not properly configured yet. Please make sure the OPENROUTER_API_KEY is set in the environment variables. 🔧"
        }
    
    user_data = get_user_data(current_user_email)
    
    system_prompt = """You are Wat, a friendly AI assistant that helps users understand and optimize their home energy usage. 

You have access to the user's real-time energy data including devices, usage patterns, costs, and schedules.

Be conversational, helpful, and proactive with insights. Use emojis to be friendly. Always base your responses on the actual data provided."""

    try:
        logger.info(f"Making request to OpenRouter with API key: {OPENROUTER_API_KEY[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Smart Home Energy Monitor",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User data: {user_data}\n\nUser question: {query.question}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            ai_response = response.json()['choices'][0]['message']['content']
            
            return {
                "summary": "Wat - Your Energy Assistant",
                "content": ai_response
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401:
            return {
                "summary": "Wat - Your Energy Assistant",
                "content": "I'm having authentication issues. Please check that the OPENROUTER_API_KEY is valid. 🔑"
            }
        return {
            "summary": "Wat - Your Energy Assistant",
            "content": "I'm having trouble connecting to my AI service right now. Please try again in a moment! ⚡"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "summary": "Wat - Your Energy Assistant",
            "content": "Oops! Something went wrong on my end. Please try again! 🔌"
        }

@app.get("/ai/devices")
async def get_user_devices(current_user_email: str = Depends(get_current_user_email)):
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, type, room, created_at 
                FROM devices 
                WHERE user_id = (SELECT id FROM users WHERE email = %s)
                ORDER BY room, name
            """, (current_user_email,))
            devices = cur.fetchall()
            return {
                "devices": [
                    {
                        "id": str(device[0]),
                        "name": device[1],
                        "type": device[2],
                        "room": device[3],
                        "created_at": device[4].isoformat()
                    }
                    for device in devices
                ]
            }

@app.get("/ai/dashboard")
async def get_dashboard_data(current_user_email: str = Depends(get_current_user_email)):
    user_data = get_user_data(current_user_email)
    
    return {
        "current_usage": [
            {
                "name": d["name"],
                "type": d["type"],
                "room": d["room"],
                "usage": d["current_usage_kw"]
            }
            for d in user_data["devices"]
        ],
        "today_total": user_data["usage_summary"]["today_kwh"],
        "month_total": user_data["usage_summary"]["month_kwh"],
        "estimated_monthly_cost": user_data["usage_summary"]["month_kwh"] * user_data["electricity_rate_per_kwh"]
    }

@app.get("/ai/consumption-timeline")
async def get_consumption_timeline(
    view: Literal["daily", "weekly", "monthly"] = "daily",
    current_user_email: str = Depends(get_current_user_email)
):
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (current_user_email,))
            user_result = cur.fetchone()
            if not user_result:
                raise HTTPException(status_code=404, detail="User not found")
            user_id = user_result[0]
            
            time_format = {
                "daily": ("day", "15 days", "15 days"),  # Changed from 'hour' to 'day'
                "weekly": ("week", "12 weeks", "4 weeks"),  # Changed from 'day' to 'week'
                "monthly": ("month", "12 months", "3 months")  # Changed from 'day' to 'month'
            }
            
            bucket, past_interval, future_interval = time_format[view]
            
            cur.execute(f"""
                SELECT 
                    DATE_TRUNC('{bucket}', t.timestamp) as time_bucket,
                    SUM(t.energy_usage) as total_usage
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = %s
                AND t.timestamp >= CURRENT_TIMESTAMP - INTERVAL '{past_interval}'
                GROUP BY time_bucket
                ORDER BY time_bucket
            """, (user_id,))
            
            historical_data = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    ds.day_of_week,
                    ds.start_hour,
                    ds.end_hour,
                    ds.power_consumption
                FROM device_schedules ds
                JOIN devices d ON ds.device_id = d.id
                WHERE d.user_id = %s
            """, (user_id,))
            
            schedules = cur.fetchall()
            
            now = datetime.now()
            forecast_data = []
            
            if view == "daily":
                # Show 15 days into the future
                for days_ahead in range(1, 16):  # Next 15 days
                    daily_usage = 0
                    future_date = now + timedelta(days=days_ahead)
                    day_of_week = (future_date.weekday() + 1) % 7
                    
                    # Calculate daily usage based on schedules
                    for sched_day, start, end, power in schedules:
                        if sched_day == day_of_week:
                            daily_usage += (end - start) * power
                    
                    forecast_data.append({
                        "timestamp": future_date.replace(hour=12).isoformat(),  # Noon of each day
                        "usage": daily_usage,
                        "is_forecast": True
                    })
            elif view == "weekly":
                # Show 4 weeks into the future
                for weeks_ahead in range(1, 5):
                    future_date = now + timedelta(weeks=weeks_ahead)
                    week_usage = 0
                    
                    for day in range(7):
                        day_of_week = ((future_date + timedelta(days=day)).weekday() + 1) % 7
                        daily_usage = 0
                        for sched_day, start, end, power in schedules:
                            if sched_day == day_of_week:
                                daily_usage += (end - start) * power
                        week_usage += daily_usage
                    
                    forecast_data.append({
                        "timestamp": future_date.isoformat(),
                        "usage": week_usage / 7,
                        "is_forecast": True
                    })
            else:
                # Show 3 months into the future
                for months_ahead in range(1, 4):
                    future_date = now + timedelta(days=30 * months_ahead)
                    monthly_usage = 0
                    
                    for day in range(30):
                        day_of_week = ((future_date + timedelta(days=day)).weekday() + 1) % 7
                        daily_usage = 0
                        for sched_day, start, end, power in schedules:
                            if sched_day == day_of_week:
                                daily_usage += (end - start) * power
                        monthly_usage += daily_usage
                    
                    forecast_data.append({
                        "timestamp": future_date.isoformat(),
                        "usage": monthly_usage / 30,
                        "is_forecast": True
                    })
            
            return {
                "historical": [
                    {
                        "timestamp": row[0].isoformat(),
                        "usage": float(row[1]),
                        "is_forecast": False
                    }
                    for row in historical_data
                ],
                "forecast": forecast_data,
                "view": view
            }