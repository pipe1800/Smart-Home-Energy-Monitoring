import os
import psycopg2
import httpx
import json
import traceback  # <-- ADD THIS IMPORT
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional, Literal

# Load environment variables
load_dotenv()

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

Here are the available tools:
- `LIST_DEVICES`: Use when the user asks for a list of their devices.
- `SUM`: Use for calculating total energy usage. Requires `device_name`.
- `AVG`: Use for calculating average energy usage. Requires `device_name`.
- `TIME_SERIES`: Use for getting detailed usage over time. Requires `device_name`.

If the user asks "which of my devices is using the most power?", use the `LIST_DEVICES` query type.
Analyze the user's question and respond only with the appropriate JSON object.
"""

@app.get("/ai")
def read_root():
    return {"status": "AI Service is running"}

@app.post("/ai/query")
async def handle_query(query: QueryRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct-v0.2",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query.question}
                    ],
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0 # Add a timeout
            )
            response.raise_for_status()
            llm_output_str = response.json()['choices'][0]['message']['content']
            llm_data = json.loads(llm_output_str)
            
            validated_llm_response = LLMResponse.model_validate(llm_data)

    except (httpx.HTTPStatusError, json.JSONDecodeError, Exception) as e:
        traceback.print_exc() # <-- ADD THIS LINE
        raise HTTPException(status_code=500, detail=f"Error processing LLM response: {str(e)}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            user_id_sql = "(SELECT id FROM users WHERE email = 'test@example.com')"
            
            if validated_llm_response.query_type == "LIST_DEVICES":
                sql = f"SELECT name, id FROM devices WHERE user_id = {user_id_sql};"
                cur.execute(sql)
                results = cur.fetchall()
                response_data = [{"name": row[0], "id": row[1]} for row in results]
                return {"summary": "Here are your devices:", "data": response_data}

            # All other queries require a device name
            if not validated_llm_response.params.device_name:
                raise HTTPException(status_code=400, detail="Query type requires a device_name.")

            device_name = validated_llm_response.params.device_name
            
            if validated_llm_response.query_type in ["SUM", "AVG", "TIME_SERIES"]:
                # Use a parameterized query for the device name to prevent SQL injection
                base_sql = "SELECT {agg_func} FROM telemetry t JOIN devices d ON t.device_id = d.id WHERE d.name = %s AND d.user_id = " + user_id_sql
                
                if validated_llm_response.query_type == "SUM":
                    sql = base_sql.format(agg_func="SUM(t.energy_usage)")
                elif validated_llm_response.query_type == "AVG":
                    sql = base_sql.format(agg_func="AVG(t.energy_usage)")
                elif validated_llm_response.query_type == "TIME_SERIES":
                    sql = base_sql.format(agg_func="t.timestamp, t.energy_usage") + " ORDER BY t.timestamp;"

                cur.execute(sql, (device_name,))
                results = cur.fetchall()

                if validated_llm_response.query_type == "TIME_SERIES":
                     return {"summary": f"Time series data for {device_name}", "data": [{"timestamp": r[0].isoformat(), "usage": r[1]} for r in results]}
                else:
                     return {"summary": f"{validated_llm_response.query_type} usage for {device_name}", "value": results[0][0]}

    except Exception as e:
        traceback.print_exc() # <-- ADD THIS LINE
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

    return {"detail": "Query type not implemented"}