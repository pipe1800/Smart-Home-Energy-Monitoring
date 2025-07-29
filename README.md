# Smart Home Energy Monitoring with Conversational AI

A comprehensive platform that helps users monitor and understand their energy consumption patterns with the assistance of **Wat**, an AI-powered energy advisor 🤖⚡️

## 🚀 Quick Start (One Command!)

```bash
# Clone the repository
git clone https://github.com/pipe1800/Smart-Home-Energy-Monitoring-with-Conversational-AI.git
cd Smart-Home-Energy-Monitoring-with-Conversational-AI

# Run the automated setup (builds, starts everything, and opens browser)
./setup.sh
```

The setup script will:
- ✅ Configure environment variables
- ✅ Build all Docker containers
- ✅ Start backend services (database, auth, telemetry, AI)
- ✅ Install frontend dependencies
- ✅ Start the React development server
- ✅ Wait for all services to be healthy
- ✅ Automatically open your browser

## 🛑 Stopping the Application

```bash
# Stop all services cleanly
./stop.sh
```

## 📋 Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ and npm
- 8GB RAM minimum
- Ports 3000, 8000-8002, and 5433 available

## 🏗️ Architecture

- **Frontend**: React with Tailwind CSS (port 3000)
- **Auth Service**: FastAPI authentication (port 8000)
- **Telemetry Service**: FastAPI data collection (port 8001)
- **AI Service**: FastAPI with OpenRouter integration (port 8002)
- **Database**: PostgreSQL (port 5433)

## 🧪 Test Credentials

After starting the services, you can create a new account or use:
- **Email**: test@example.com
- **Password**: testpassword123

## 💡 Key Features

- **Real-time Energy Dashboard** - Monitor consumption across all devices
- **AI Assistant "Wat"** - Conversational AI for energy insights and forecasting
- **Device Management** - Add, configure, and schedule smart home devices
- **Consumption Forecasting** - Predict monthly costs based on usage patterns
- **Cost Estimation** - Track spending and optimize energy usage
- **Smart Scheduling** - Automated device scheduling for peak hour optimization

## 🤖 Meet Wat - Your Energy Assistant

Wat is your friendly AI energy assistant that can help you:
- Analyze current energy consumption
- Provide monthly cost projections
- Suggest energy-saving strategies
- Answer questions about device usage
- Offer smart home automation tips

Try asking Wat:
- "Hello Wat, how's my energy usage today?"
- "What will my monthly bill be?"
- "Which device uses the most energy?"
- "Give me some energy saving tips"

## 🔧 Development Setup

For development purposes:
```bash
# Install dependencies
cd frontend && npm install

# Run services individually
docker-compose up db -d
cd backend/auth_service && python main.py
cd backend/telemetry_service && python main.py
cd backend/ai_service && python main.py
cd frontend && npm start
```

## 🛠️ Troubleshooting

**Services won't start:**
```bash
# Check backend logs
docker-compose logs -f [service_name]

# Check frontend logs
tail -f frontend.log
```

**Reset everything:**
```bash
# Stop all services
./stop.sh

# Clean up and restart
docker-compose down -v
./setup.sh
```

**Port conflicts:**
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000-8002
lsof -i :5433
```

**Frontend issues:**
```bash
# Manual frontend setup
cd frontend
npm install
npm start
```

## 🔐 Security Note

This project includes a demo API key in `.env.example` for testing convenience. In production:
- Use your own OpenRouter API key
- Implement proper key rotation
- Use environment-specific configurations
- Enable SSL/TLS encryption

## 📊 Sample Data

The application includes sample devices and schedules for demonstration:
- Living Room AC
- Kitchen Refrigerator  
- Master Bedroom Light
- Smart Thermostat
- Home Office Outlet
- Washing Machine

## 🎯 Technical Highlights

- **Microservices Architecture** with Docker containers
- **JWT Authentication** with secure token management
- **Real-time Data Processing** with PostgreSQL
- **AI Integration** using OpenRouter and Claude
- **Responsive Design** with Tailwind CSS
- **RESTful APIs** with FastAPI
- **Database Migrations** and health checks
- **Rate Limiting** and error handling
