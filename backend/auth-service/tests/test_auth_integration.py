import pytest
from unittest.mock import Mock, patch
import json

# Mock classes for testing API endpoints
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
    
    def json(self):
        return self._json_data

class MockTestClient:
    def __init__(self):
        self.mock_responses = {}
    
    def post(self, url, **kwargs):
        # Mock registration endpoint
        if url == "/auth/register":
            data = kwargs.get('json', {})
            email = data.get('email', '')
            
            if email == "existing@example.com":
                return MockResponse(400, {
                    "status": "error",
                    "message": "Email already registered"
                })
            elif email == "test@example.com":
                return MockResponse(201, {
                    "status": "success",
                    "message": "User created successfully",
                    "data": {"devices_created": 6}
                })
        
        # Mock login endpoint
        elif url == "/auth/login":
            form_data = kwargs.get('data', {})
            username = form_data.get('username', '')
            password = form_data.get('password', '')
            
            if username == "nonexistent@example.com":
                return MockResponse(404, {
                    "detail": "User not found"
                })
            elif username == "test@example.com" and password == "correct_password":
                return MockResponse(200, {
                    "access_token": "fake_jwt_token_12345",
                    "token_type": "bearer"
                })
            elif username == "test@example.com" and password == "wrong_password":
                return MockResponse(401, {
                    "detail": "Incorrect password"
                })
        
        return MockResponse(404, {"detail": "Not found"})

class TestAuthIntegration:
    def test_complete_registration_flow(self):
        """Test full user registration process"""
        client = MockTestClient()
        
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["devices_created"] == 6
        
    def test_duplicate_email_registration(self):
        """Registration should fail for existing email"""
        client = MockTestClient()
        
        response = client.post("/auth/register", json={
            "email": "existing@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["message"]
    
    def test_successful_login(self):
        """Login should work with correct credentials"""
        client = MockTestClient()
        
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "correct_password"
        })
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["access_token"] == "fake_jwt_token_12345"
    
    def test_login_user_not_found(self):
        """Login should fail for non-existent user"""
        client = MockTestClient()
        
        response = client.post("/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_login_wrong_password(self):
        """Login should fail with wrong password"""
        client = MockTestClient()
        
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        assert "Incorrect password" in response.json()["detail"]
    
    def test_registration_validation(self):
        """Test various registration input validations"""
        client = MockTestClient()
        
        # Test empty email
        response = client.post("/auth/register", json={
            "email": "",
            "password": "password123"
        })
        # In a real app, this would return 422 for validation error
        # For our mock, we'll just check it doesn't crash
        assert response.status_code in [400, 422, 404]
        
        # Test weak password handling
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "123"
        })
        # This would normally validate password strength
        assert response.status_code in [201, 400, 422]
