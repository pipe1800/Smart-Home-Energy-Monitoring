#!/bin/bash

echo "🏠 Smart Home Energy Monitoring Setup"
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Setting up environment variables..."
    cp .env.example .env
    echo "✅ Environment file created from .env.example"
else
    echo "ℹ️  Environment file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Function to check if a port is open
check_port() {
    nc -z localhost $1 2>/dev/null
    return $?
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "⏳ Waiting for $service_name..."
    
    while ! check_port $port; do
        if [ $attempt -eq $max_attempts ]; then
            echo " ❌ Failed (timeout)"
            return 1
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo " ✅ Ready!"
    return 0
}

# Build and start backend services
echo "🔨 Building Docker services..."
docker-compose build

echo "🚀 Starting backend services..."
docker-compose up -d

# Wait for each backend service
echo ""
echo "🔍 Checking backend services..."
wait_for_service "Database" 5433
wait_for_service "Auth Service" 8000
wait_for_service "Telemetry Service" 8001
wait_for_service "AI Service (Wat)" 8002

# Check if all backend services are healthy
echo ""
echo "📊 Backend service status:"
docker-compose ps

# Install frontend dependencies and start
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
else
    echo "ℹ️  Frontend dependencies already installed"
fi

# Start frontend in background
echo "🚀 Starting frontend development server..."
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Store the PID for later
echo $FRONTEND_PID > ../frontend.pid

cd ..

# Wait for frontend to be ready
echo ""
wait_for_service "Frontend" 3000

# Give it a few more seconds to fully initialize
sleep 3

# Check if frontend is actually running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check frontend.log for details."
    exit 1
fi

# Open browser
echo ""
echo "🌐 Opening browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:3000
    elif command -v gnome-open > /dev/null; then
        gnome-open http://localhost:3000
    else
        echo "⚠️  Could not detect browser. Please open http://localhost:3000 manually."
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start http://localhost:3000
fi

echo ""
echo "✅ Setup complete! Your Smart Home Energy Monitor is running:"
echo ""
echo "🌐 Frontend:         http://localhost:3000"
echo "🔐 Auth Service:     http://localhost:8000/docs"
echo "📊 Telemetry:        http://localhost:8001/docs"
echo "🤖 AI Service (Wat): http://localhost:8002/docs"
echo "🗄️  Database:         localhost:5433"
echo ""
echo "💡 You can create a new account or use test credentials"
echo "📧 Email: test@example.com"
echo "🔑 Password: testpassword123"
echo ""
echo "🛑 To stop all services: ./stop.sh"
echo "🔄 To restart: docker-compose restart && npm start --prefix frontend"
echo "📋 To view backend logs: docker-compose logs -f [service_name]"
echo "📋 To view frontend logs: tail -f frontend.log"
