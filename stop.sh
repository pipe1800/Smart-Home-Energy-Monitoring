#!/bin/bash

echo "🛑 Stopping Smart Home Energy Monitor..."

# Stop frontend if running
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🛑 Stopping frontend..."
        kill $FRONTEND_PID
        rm frontend.pid
    fi
fi

# Stop Docker services
echo "🛑 Stopping backend services..."
docker-compose down

# Clean up log files
if [ -f frontend.log ]; then
    rm frontend.log
fi

echo "✅ All services stopped!"
