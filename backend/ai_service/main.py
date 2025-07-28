import os
import psycopg2
import httpx
import json
import jwt
import traceback  
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional, Literal


load_dotenv()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_email(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class QueryRequest(BaseModel):
    question: str

class LLMParams(BaseModel):
    device_name: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None

class LLMResponse(BaseModel):
    query_type: Literal['SUM', 'AVG', 'LIST_DEVICES', 'TIME_SERIES']
    params: LLMParams

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="smart_home_db",
        port="5432"
    )
    return conn

SYSTEM_PROMPT = """
You are a smart home data analyst. Your job is to take a user's question and convert it into a structured JSON object.
You must only respond with JSON. The JSON object must conform to the following Pydantic models:

class LLMParams(BaseModel):
    device_name: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None

class LLMResponse(BaseModel):
    query_type: Literal['SUM', 'AVG', 'LIST_DEVICES', 'TIME_SERIES']
    params: LLMParams

Here are the available query types and when to use them:
- `LIST_DEVICES`: Use ONLY when the user explicitly asks for a list of all their devices, such as "what devices do I have?", "list my devices", "show me all devices"
- `SUM`: Use for calculating total energy usage for a specific device. Example: "total usage of Living Room AC", "how much energy has the refrigerator used?"
- `AVG`: Use for calculating average energy usage for a specific device. Example: "average usage of thermostat", "what's the average consumption of my washing machine?"
- `TIME_SERIES`: Use for getting detailed usage over time for a specific device. Example: "show me AC usage over time", "energy consumption pattern for bedroom light"

Important rules:
1. If the user mentions a specific device name, extract it and use SUM, AVG, or TIME_SERIES based on what they're asking
2. Only use LIST_DEVICES when they explicitly ask for all devices
3. Default to TIME_SERIES if they mention a device but the intent is unclear
4. Device names are case-sensitive and should match exactly: "Living Room AC", "Kitchen Refrigerator", "Master Bedroom Light", "Smart Thermostat", "Home Office Outlet", "Washing Machine"

Examples:
- "How much energy is my Living Room AC using?" -> {"query_type": "SUM", "params": {"device_name": "Living Room AC"}}
- "Show me all my devices" -> {"query_type": "LIST_DEVICES", "params": {}}
- "What's the average usage of the refrigerator?" -> {"query_type": "AVG", "params": {"device_name": "Kitchen Refrigerator"}}
- "Show me the thermostat data" -> {"query_type": "TIME_SERIES", "params": {"device_name": "Smart Thermostat"}}
"""

@app.get("/ai")
def read_root():
    return {"status": "AI Service is running"}

@app.post("/ai/query")
async def handle_query(query: QueryRequest, current_user_email: str = Depends(get_current_user_email)):
    print(f"User query: {query.question}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Smart Home Energy Monitor"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct-v0.2",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query.question}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,  
                    "max_tokens": 150
                },
                timeout=30.0
            )
            response.raise_for_status()
            llm_output_str = response.json()['choices'][0]['message']['content']
            print(f"LLM response: {llm_output_str}")
            
            llm_data = json.loads(llm_output_str)
            validated_llm_response = LLMResponse.model_validate(llm_data)
            print(f"Parsed query type: {validated_llm_response.query_type}")
            print(f"Parsed params: {validated_llm_response.params}")

    except (httpx.HTTPStatusError, json.JSONDecodeError, Exception) as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing LLM response: {str(e)}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get user ID
            cur.execute("SELECT id FROM users WHERE email = %s", (current_user_email,))
            user_id = cur.fetchone()[0]
            
            if validated_llm_response.query_type == "LIST_DEVICES":
                cur.execute(
                    "SELECT name, id, type, room FROM devices WHERE user_id = %s ORDER BY room, name;",
                    (user_id,)
                )
                results = cur.fetchall()
                response_data = [
                    {
                        "name": row[0], 
                        "id": str(row[1]),
                        "type": row[2],
                        "room": row[3]
                    } 
                    for row in results
                ]
                return {"summary": "Here are your devices:", "data": response_data}

            # All other queries require a device name
            if not validated_llm_response.params.device_name:
                raise HTTPException(status_code=400, detail="Query type requires a device_name.")

            device_name = validated_llm_response.params.device_name
            
            cur.execute(
                "SELECT id FROM devices WHERE name = %s AND user_id = %s",
                (device_name, user_id)
            )
            device_result = cur.fetchone()
            if not device_result:
                return {
                    "summary": f"Device '{device_name}' not found. Please use one of your registered devices.",
                    "data": []
                }
            
            device_id = device_result[0]
            
            if validated_llm_response.query_type == "SUM":
                cur.execute(
                    "SELECT COALESCE(SUM(energy_usage), 0) FROM telemetry WHERE device_id = %s",
                    (device_id,)
                )
                result = cur.fetchone()[0]
                return {
                    "summary": f"Total energy usage for {device_name}",
                    "value": float(result)
                }
                
            elif validated_llm_response.query_type == "AVG":
                cur.execute(
                    "SELECT COALESCE(AVG(energy_usage), 0) FROM telemetry WHERE device_id = %s",
                    (device_id,)
                )
                result = cur.fetchone()[0]
                return {
                    "summary": f"Average energy usage for {device_name}",
                    "value": float(result)
                }
                
            elif validated_llm_response.query_type == "TIME_SERIES":
                cur.execute(
                    """
                    SELECT timestamp, energy_usage 
                    FROM telemetry 
                    WHERE device_id = %s 
                    AND timestamp > NOW() - INTERVAL '24 hours'
                    ORDER BY timestamp DESC
                    LIMIT 24
                    """,
                    (device_id,)
                )
                results = cur.fetchall()
                return {
                    "summary": f"Energy usage over time for {device_name}",
                    "data": [
                        {
                            "timestamp": r[0].isoformat(),
                            "usage": float(r[1])
                        } 
                        for r in results
                    ]
                }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

    return {"detail": "Query type not implemented"}

@app.get("/ai/devices")
async def get_user_devices(current_user_email: str = Depends(get_current_user_email)):
    """Get all devices for the current user"""
    conn = get_db_connection()
    try:
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
    finally:
        conn.close()

@app.get("/ai/dashboard")
async def get_dashboard_data(current_user_email: str = Depends(get_current_user_email)):
    """Get dashboard summary data"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get current usage by device
            cur.execute("""
                SELECT d.name, d.type, d.room, t.energy_usage
                FROM devices d
                JOIN LATERAL (
                    SELECT energy_usage 
                    FROM telemetry 
                    WHERE device_id = d.id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ) t ON true
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
            """, (current_user_email,))
            current_usage = cur.fetchall()
            
            # Get today's total usage
            cur.execute("""
                SELECT COALESCE(SUM(t.energy_usage), 0)
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
                AND t.timestamp >= CURRENT_DATE
            """, (current_user_email,))
            today_total = cur.fetchone()[0]
            
            # Get this month's total
            cur.execute("""
                SELECT COALESCE(SUM(t.energy_usage), 0)
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
                AND t.timestamp >= DATE_TRUNC('month', CURRENT_DATE)
            """, (current_user_email,))
            month_total = cur.fetchone()[0]
            
            return {
                "current_usage": [
                    {
                        "name": device[0],
                        "type": device[1],
                        "room": device[2],
                        "usage": float(device[3])
                    }
                    for device in current_usage
                ],
                "today_total": float(today_total),
                "month_total": float(month_total),
                "estimated_monthly_cost": float(month_total) * 0.12  # $0.12 per kWh
            }
    finally:
        conn.close()