import os
import httpx
import json
import traceback
from fastapi import FastAPI, HTTPException, Request, status, Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional, Literal, Union
from datetime import datetime, timedelta

from shared.auth import get_current_user_email
from shared.database import db_pool
from shared.models import success_response
from shared.utils import setup_cors, setup_exception_handlers, setup_logging
from shared.rate_limiting import ai_rate_limiter

load_dotenv()

# Setup logging
logger = setup_logging("ai_service")

class QueryRequest(BaseModel):
    question: str

class LLMParams(BaseModel):
    device_name: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None

class DataQuery(BaseModel):
    query_type: Literal['SUM', 'AVG', 'LIST_DEVICES', 'TIME_SERIES']
    params: LLMParams

class GeneralResponse(BaseModel):
    response_type: Literal['GENERAL']
    content: str

class LLMResponse(BaseModel):
    intent_type: Literal['DATA_QUERY', 'GENERAL_ADVICE']
    data_query: Optional[DataQuery] = None
    general_response: Optional[GeneralResponse] = None

app = FastAPI(title="AI Service", version="1.0.0")

# Setup middleware and exception handlers
setup_cors(app)
setup_exception_handlers(app)

def calculate_monthly_projection(device_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT day_of_week, start_hour, end_hour, power_consumption 
               FROM device_schedules WHERE device_id = %s""",
            (device_id,)
        )
        schedule = cur.fetchall()
        
        if not schedule:
            # Use historical average if no schedule
            cur.execute(
                """SELECT AVG(energy_usage) * 24 * 30
                FROM telemetry 
                WHERE device_id = %s
                AND timestamp >= NOW() - INTERVAL '30 days'""",
                (device_id,)
            )
            result = cur.fetchone()
            return float(result[0]) if result[0] else 0
        
        # Calculate based on schedule
        weekly_kwh = 0
        for day, start, end, power in schedule:
            hours = end - start if end > start else 0
            weekly_kwh += hours * power
        
        # 4.33 weeks in a month on average
        return weekly_kwh * 4.33

SYSTEM_PROMPT = """
You are an AI energy assistant for a smart home monitoring system. You help users understand their energy usage and provide comprehensive advice about energy-related topics.

IMPORTANT: You have access to the user's actual device data, historical usage, and schedules. When asked about forecasts or projections, you should:
1. Use the SUM query to get current month-to-date usage
2. Calculate the monthly projection based on device schedules
3. Provide a specific forecast based on their actual data

The user has the following devices with schedules:
- Living Room AC: Runs evenings (6-10 PM weekdays, 12-11 PM weekends) at 3.5 kW
- Kitchen Refrigerator: Runs continuously at 0.5 kW
- Master Bedroom Light: Runs evenings (8-11 PM) at 0.06 kW
- Smart Thermostat: Runs mornings (6-9 AM) and evenings (5-10 PM) at 2.0 kW
- Home Office Outlet: Runs weekdays (9 AM-5 PM) at 0.3 kW
- Washing Machine: Runs Tuesday and Friday (10 AM-12 PM) at 2.0 kW

When asked about monthly forecasts, projections, or "what will my bill be", respond with:
{
    "intent_type": "DATA_QUERY",
    "data_query": {
        "query_type": "SUM",
        "params": {
            "device_name": null,
            "time_start": null,
            "time_end": null
        }
    }
}

This will calculate the total forecast for all devices based on their schedules.

For data queries about specific devices:
{
    "intent_type": "DATA_QUERY",
    "data_query": {
        "query_type": "SUM" | "AVG" | "LIST_DEVICES" | "TIME_SERIES",
        "params": {
            "device_name": "Device Name" | null,
            "time_start": null,
            "time_end": null
        }
    }
}

For any other energy-related questions, advice, or estimates:
{
    "intent_type": "GENERAL_ADVICE",
    "general_response": {
        "response_type": "GENERAL",
        "content": "Your comprehensive response here"
    }
}
- Discuss renewable energy options
- Explain smart home automation benefits

Be conversational, helpful, and provide actionable advice. Use the user's context when available.
"""

@app.get("/ai")
def read_root():
    return {"status": "AI Service is running"}

@app.post("/ai/query")
async def handle_query(query: QueryRequest, current_user_email: str = Depends(get_current_user_email)):
    # Apply rate limiting
    ai_rate_limiter.check_rate_limit(current_user_email)
    
    logger.info(f"User query from {current_user_email}: {query.question}")
    
    # Get user's actual devices for the prompt
    device_info = ""
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.name, d.type, d.room, 
                       COALESCE(ds.start_hour, 0) as start_hour,
                       COALESCE(ds.end_hour, 0) as end_hour,
                       COALESCE(ds.power_consumption, d.power_rating) as power
                FROM devices d
                LEFT JOIN device_schedules ds ON d.id = ds.device_id
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
                ORDER BY d.name, ds.day_of_week
            """, (current_user_email,))
            devices = cur.fetchall()
            
            if devices:
                device_list = {}
                for name, dtype, room, start, end, power in devices:
                    if name not in device_list:
                        device_list[name] = f"- {name}: {dtype} in {room.replace('_', ' ')}"
                device_info = "\n".join(device_list.values())
            else:
                device_info = "- No devices configured yet"
    
    # Build dynamic system prompt
    DYNAMIC_SYSTEM_PROMPT = f"""
You are Wat, a friendly and knowledgeable AI energy assistant for a smart home monitoring system. Your personality is warm, helpful, and enthusiastic about helping users understand and optimize their energy usage.

IMPORTANT: You have access to the user's actual device data, historical usage, and schedules. 

The user has the following devices:
{device_info}

When responding to users:
1. Always introduce yourself as Wat if it's a greeting or first interaction
2. Be conversational and friendly while staying focused on energy-related topics
3. For general conversation, energy questions, tips, or advice, use GENERAL_ADVICE
4. Only use DATA_QUERY when the user specifically asks about their devices, usage, or costs

Response formats:

For monthly forecasts, projections, cost estimates, or anything about "monthly" consumption/costs:
{{
    "intent_type": "DATA_QUERY",
    "data_query": {{
        "query_type": "SUM",
        "params": {{
            "device_name": null,
            "time_start": null,
            "time_end": null
        }}
    }}
}}

For data queries about specific devices, use their exact name from above:
{{
    "intent_type": "DATA_QUERY",
    "data_query": {{
        "query_type": "SUM" | "AVG" | "LIST_DEVICES" | "TIME_SERIES",
        "params": {{
            "device_name": "Exact Device Name" | null,
            "time_start": null,
            "time_end": null
        }}
    }}
}}

For greetings, general energy conversation, tips, advice, or any non-specific queries:
{{
    "intent_type": "GENERAL_ADVICE",
    "general_response": {{
        "response_type": "GENERAL",
        "content": "Your friendly, conversational response here"
    }}
}}

Remember:
- Greet users warmly and introduce yourself as Wat
- Always be helpful and encouraging about energy savings
- Use emojis sparingly to be friendly (⚡️ 💡 🌱 ♻️)
- If users ask non-energy questions, gently redirect to energy topics
- For ANY question about monthly costs, forecasts, or projections, use DATA_QUERY
- Match device names exactly as shown above
"""
    
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
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": DYNAMIC_SYSTEM_PROMPT},
                        {"role": "user", "content": query.question}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 800
                },
                timeout=30.0
            )
            response.raise_for_status()
            llm_output_str = response.json()['choices'][0]['message']['content']
            print(f"LLM response: {llm_output_str}")
            
            llm_data = json.loads(llm_output_str)
            validated_llm_response = LLMResponse.model_validate(llm_data)
            print(f"Intent type: {validated_llm_response.intent_type}")

    except (httpx.HTTPStatusError, json.JSONDecodeError, Exception) as e:
        traceback.print_exc()
        # Improved fallback for parsing errors
        if "monthly" in query.question.lower() or "forecast" in query.question.lower() or "bill" in query.question.lower():
            # Force a monthly forecast query
            validated_llm_response = LLMResponse(
                intent_type="DATA_QUERY",
                data_query=DataQuery(
                    query_type="SUM",
                    params=LLMParams(device_name=None, time_start=None, time_end=None)
                )
            )
        else:
            # Default to a friendly general response instead of an error
            validated_llm_response = LLMResponse(
                intent_type="GENERAL_ADVICE",
                general_response=GeneralResponse(
                    response_type="GENERAL",
                    content="Hi there! I'm Wat, your friendly energy assistant! ⚡️ I'm here to help you understand and optimize your home's energy usage. You can ask me about:\n\n• Your current energy consumption\n• Monthly cost projections\n• Device-specific usage patterns\n• Energy-saving tips and tricks\n• Smart home automation ideas\n• Peak hours and rate optimization\n\nWhat would you like to know about your energy usage today?"
                )
            )

    if validated_llm_response.intent_type == "GENERAL_ADVICE":
        return {
            "summary": "Wat - Your Energy Assistant",
            "content": validated_llm_response.general_response.content
        }
    
    if validated_llm_response.intent_type == "DATA_QUERY":
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (current_user_email,))
                user_id = cur.fetchone()[0]
                
                data_query = validated_llm_response.data_query
                
                if data_query.query_type == "LIST_DEVICES":
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
                    return {"summary": "Your Smart Home Devices", "data": response_data}

                if not data_query.params.device_name:
                    # Handle total forecast for all devices
                    if data_query.query_type == "SUM":
                        # Calculate total forecast for all devices
                        cur.execute("""
                            SELECT id, name
                            FROM devices 
                            WHERE user_id = %s
                        """, (user_id,))
                        all_devices = cur.fetchall()
                        
                        total_monthly_projection = 0
                        total_current_usage = 0
                        
                        for device_id, device_name in all_devices:
                            # Get current month usage
                            cur.execute("""
                                SELECT COALESCE(SUM(energy_usage), 0)
                                FROM telemetry 
                                WHERE device_id = %s
                                AND timestamp >= DATE_TRUNC('month', CURRENT_DATE)
                            """, (device_id,))
                            device_current = float(cur.fetchone()[0])
                            total_current_usage += device_current
                            
                            # Get projected monthly usage
                            device_projection = calculate_monthly_projection(device_id, conn)
                            total_monthly_projection += device_projection
                        
                        total_current_cost = total_current_usage * 0.12
                        total_monthly_cost = total_monthly_projection * 0.12
                        
                        from datetime import datetime
                        days_in_month = 30
                        days_passed = datetime.now().day
                        days_remaining = days_in_month - days_passed
                        
                        return {
                            "summary": "Monthly Energy Forecast",
                            "content": f"Based on your device schedules, your projected monthly usage is {total_monthly_projection:.2f} kWh (${total_monthly_cost:.2f}). So far this month, you've used {total_current_usage:.2f} kWh (${total_current_cost:.2f}) with {days_remaining} days remaining.",
                            "value": total_monthly_projection,
                            "unit": "kWh",
                            "cost": f"${total_monthly_cost:.2f}",
                            "current_usage": f"{total_current_usage:.2f} kWh",
                            "current_cost": f"${total_current_cost:.2f}",
                            "additional_info": f"This projection is based on your configured device schedules. Actual usage may vary."
                        }
                    else:
                        return {
                            "summary": "Please specify a device",
                            "content": "I need to know which device you're asking about. You have: Living Room AC, Kitchen Refrigerator, Master Bedroom Light, Smart Thermostat, Home Office Outlet, and Washing Machine."
                        }

                device_name = data_query.params.device_name
                
                cur.execute(
                    "SELECT id FROM devices WHERE name = %s AND user_id = %s",
                    (device_name, user_id)
                )
                device_result = cur.fetchone()
                if not device_result:
                    return {
                        "summary": f"Device not found",
                        "content": f"I couldn't find '{device_name}' in your devices. Your available devices are: Living Room AC, Kitchen Refrigerator, Master Bedroom Light, Smart Thermostat, Home Office Outlet, and Washing Machine."
                    }
                
                device_id = device_result[0]
                
                if data_query.query_type == "SUM":
                    cur.execute(
                        """
                        SELECT COALESCE(SUM(energy_usage), 0),
                               COUNT(*) as reading_count,
                               MIN(timestamp) as first_reading,
                               MAX(timestamp) as last_reading
                        FROM telemetry 
                        WHERE device_id = %s
                        """,
                        (device_id,)
                    )
                    result = cur.fetchone()
                    total_kwh = float(result[0])
                    reading_count = result[1]
                    first_reading = result[2]
                    last_reading = result[3]
                    
                    actual_cost = total_kwh * 0.12
                    
                    monthly_projection = calculate_monthly_projection(device_id, conn)
                    monthly_cost_projection = monthly_projection * 0.12
                    
                    days_tracked = (last_reading - first_reading).days + 1 if first_reading else 0
                    
                    return {
                        "summary": f"Energy usage for {device_name}",
                        "value": total_kwh,
                        "unit": "kWh",
                        "cost": f"${actual_cost:.2f}",
                        "monthly_projection": f"${monthly_cost_projection:.2f}",
                        "additional_info": f"Actual usage: {total_kwh:.2f} kWh over {days_tracked} days (${actual_cost:.2f}). Projected monthly: {monthly_projection:.2f} kWh (${monthly_cost_projection:.2f})"
                    }
                    
                elif data_query.query_type == "AVG":
                    cur.execute(
                        """
                        SELECT COALESCE(AVG(energy_usage), 0),
                               COUNT(DISTINCT DATE_TRUNC('day', timestamp))
                        FROM telemetry 
                        WHERE device_id = %s
                        """,
                        (device_id,)
                    )
                    result = cur.fetchone()
                    avg_usage = float(result[0])
                    days_tracked = result[1]
                    monthly_estimate = avg_usage * 24 * 30 * 0.12
                    
                    return {
                        "summary": f"Average energy usage for {device_name}",
                        "value": avg_usage,
                        "unit": "kW",
                        "monthly_estimate": f"${monthly_estimate:.2f}",
                        "additional_info": f"Based on {days_tracked} days of data, estimated monthly cost: ${monthly_estimate:.2f}"
                    }
                    
                elif data_query.query_type == "TIME_SERIES":
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
                    
                    total_24h = sum(r[1] for r in results)
                    daily_cost = total_24h * 0.12
                    
                    return {
                        "summary": f"24-hour usage pattern for {device_name}",
                        "data": [
                            {
                                "timestamp": r[0].isoformat(),
                                "usage": float(r[1])
                            } 
                            for r in results
                        ],
                        "daily_total": f"{total_24h:.2f} kWh",
                        "daily_cost": f"${daily_cost:.2f}",
                        "additional_info": f"Yesterday's cost: ${daily_cost:.2f} (${daily_cost * 365:.2f}/year at this rate)"
                    }

    return {"detail": "Query type not implemented"}

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
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all devices with their latest usage (or 0 if no telemetry)
            cur.execute("""
                SELECT d.name, d.type, d.room, COALESCE(t.energy_usage, 0) as usage
                FROM devices d
                LEFT JOIN LATERAL (
                    SELECT energy_usage 
                    FROM telemetry 
                    WHERE device_id = d.id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ) t ON true
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
                ORDER BY d.room, d.name
            """, (current_user_email,))
            current_usage = cur.fetchall()
            
            cur.execute("""
                SELECT COALESCE(SUM(t.energy_usage), 0)
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.user_id = (SELECT id FROM users WHERE email = %s)
                AND t.timestamp >= CURRENT_DATE
            """, (current_user_email,))
            today_total = cur.fetchone()[0]
            
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
                "estimated_monthly_cost": float(month_total) * 0.12
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
            
            if view == "daily":
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('hour', t.timestamp) as time_bucket,
                        SUM(t.energy_usage) as total_usage
                    FROM telemetry t
                    JOIN devices d ON t.device_id = d.id
                    WHERE d.user_id = %s
                    AND t.timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """, (user_id,))
                
            elif view == "weekly":
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('day', t.timestamp) as time_bucket,
                        SUM(t.energy_usage) as total_usage
                    FROM telemetry t
                    JOIN devices d ON t.device_id = d.id
                    WHERE d.user_id = %s
                    AND t.timestamp >= NOW() - INTERVAL '12 weeks'
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """, (user_id,))
                
            else:
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('day', t.timestamp) as time_bucket,
                        SUM(t.energy_usage) as total_usage
                    FROM telemetry t
                    JOIN devices d ON t.device_id = d.id
                    WHERE d.user_id = %s
                    AND t.timestamp >= NOW() - INTERVAL '12 months'
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
                # Generate 7-day hourly forecast
                for days_ahead in range(7):
                    for hour in range(24):
                        future_datetime = now + timedelta(days=days_ahead, hours=hour)
                        day_of_week = (future_datetime.weekday() + 1) % 7
                        
                        hourly_usage = 0
                        for sched_day, start, end, power in schedules:
                            if sched_day == day_of_week and start <= hour < end:
                                hourly_usage += power
                        
                        if days_ahead > 0 or hour > now.hour:
                            forecast_data.append({
                                "timestamp": future_datetime.isoformat(),
                                "usage": hourly_usage,
                                "is_forecast": True
                            })
            elif view == "weekly":
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