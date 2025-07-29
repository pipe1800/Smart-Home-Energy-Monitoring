FROM python:3.11-slim

WORKDIR /app

# Copy shared modules first
COPY shared /app/shared

# Copy service-specific files
COPY telemetry-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telemetry-service/ .

# Add the app directory to Python path
ENV PYTHONPATH=/app:$PYTHONPATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]