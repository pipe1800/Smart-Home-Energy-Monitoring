# Telemetry Simulation Scripts

This directory contains scripts to simulate telemetry data for your smart home energy monitoring system.

## Files

- `telemetry_simulator.py` - Full-featured simulator with multiple modes
- `quick_simulate.py` - Simple script for quick data generation
- `requirements.txt` - Python dependencies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your authentication token:
```bash
export AUTH_TOKEN="your-auth-token-here"
```

## Usage

### Quick Simulation
Generate 24 hours of data with realistic patterns:
```bash
python quick_simulate.py
```

### Full Simulator

#### Historical Data Generation
```bash
# Generate 24 hours of data with 15-minute intervals
python telemetry_simulator.py --mode historical --hours 24 --interval 15

# Generate 7 days of data with 30-minute intervals
python telemetry_simulator.py --mode historical --hours 168 --interval 30
```

#### Real-time Simulation
```bash
# Run real-time simulation for 60 minutes
python telemetry_simulator.py --mode realtime --duration 60

# Run real-time simulation for 2 hours
python telemetry_simulator.py --mode realtime --duration 120
```

#### Custom Configuration
```bash
# Use custom telemetry service URL and auth token
python telemetry_simulator.py \
  --mode historical \
  --hours 48 \
  --interval 10 \
  --url http://localhost:8003 \
  --token your-custom-token
```

## Device Patterns

The simulator generates realistic consumption patterns for different device types:

- **Refrigerator**: Constant low consumption (~150W)
- **Air Conditioner**: High consumption during daytime hours (10AM-6PM)
- **Washing Machine**: Occasional use during morning and evening
- **Lighting**: Active during morning and evening hours
- **Television**: Evening entertainment hours
- **Computer**: Work hours (9AM-5PM)
- **Default**: Random consumption for unknown device types

## Prerequisites

1. Your smart home system should be running:
   - API Gateway on port 8001
   - Telemetry service on port 8003
   
2. You need a valid authentication token from logging into the system

3. You should have devices created in your account

## Getting an Auth Token

Login through your API to get a token:
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

## Troubleshooting

- **No devices found**: Make sure you have created devices in your account
- **Authentication errors**: Verify your AUTH_TOKEN is valid and not expired
- **Connection errors**: Ensure your services are running on the correct ports
- **Rate limiting**: The scripts include small delays to avoid overwhelming the server
