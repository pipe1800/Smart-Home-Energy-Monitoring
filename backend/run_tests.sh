#!/bin/bash

echo "🧪 Running Backend Tests for Auth and Telemetry Services"
echo "======================================================"

# Install test dependencies
echo "📦 Installing test dependencies..."
python3 -m pip install --user -r test-requirements.txt

# Set test environment variables
export JWT_SECRET="test_secret_key_for_testing_32_chars"
export POSTGRES_DB="test_db"
export POSTGRES_USER="test_user"
export POSTGRES_PASSWORD="test_password"
export POSTGRES_HOST="localhost"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

echo "🔍 Running unit tests..."
python3 -m pytest auth-service/tests/test_auth.py -v
python3 -m pytest telemetry-service/tests/test_telemetry.py -v

echo ""
echo "🔗 Running integration tests..."
python3 -m pytest auth-service/tests/test_auth_integration.py -v
python3 -m pytest telemetry-service/tests/test_telemetry_integration.py -v

echo ""
echo "📊 Running full test suite..."
python3 -m pytest auth-service/tests/test_auth.py -v
python3 -m pytest telemetry-service/tests/test_telemetry.py -v
python3 -m pytest auth-service/tests/test_auth_integration.py -v
python3 -m pytest telemetry-service/tests/test_telemetry_integration.py -v

echo ""
echo "✅ Tests completed!"
echo "📈 Coverage report: htmlcov/index.html"
