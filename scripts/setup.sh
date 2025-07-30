#!/bin/bash

# Telemetry Simulation Setup Script

echo "Setting up telemetry simulation environment..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if AUTH_TOKEN is set
if [ -z "$AUTH_TOKEN" ]; then
    echo "Warning: AUTH_TOKEN environment variable is not set"
    echo "You can set it with: export AUTH_TOKEN='your-token-here'"
    echo "Or get a token by logging in to your system"
fi

echo "Setup complete!"
echo ""
echo "Usage examples:"
echo "  python3 quick_simulate.py"
echo "  python3 telemetry_simulator.py --mode historical --hours 24"
echo "  python3 telemetry_simulator.py --mode realtime --duration 60"
