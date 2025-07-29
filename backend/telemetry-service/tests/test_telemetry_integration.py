import pytest
from unittest.mock import Mock
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
        self.devices = {}  # Store created devices
        self.schedules = {}  # Store device schedules
        self.telemetry = []  # Store telemetry data
    
    def post(self, url, **kwargs):
        headers = kwargs.get('headers', {})
        
        # Check for auth token (simplified)
        if 'Authorization' not in headers:
            return MockResponse(401, {"detail": "Not authenticated"})
        
        # Create device endpoint
        if url == "/devices":
            data = kwargs.get('json', {})
            device_name = data.get('name', '')
            
            if not device_name:
                return MockResponse(422, {"detail": "Validation error"})
            
            device_id = f"device-{len(self.devices) + 1}"
            self.devices[device_id] = data
            
            return MockResponse(201, {
                "status": "success",
                "data": {"id": device_id, **data}
            })
        
        # Set device schedule
        elif url.startswith("/devices/") and url.endswith("/schedule"):
            device_id = url.split("/")[2]
            schedule_data = kwargs.get('json', [])
            
            if device_id not in self.devices:
                return MockResponse(404, {"detail": "Device not found"})
            
            self.schedules[device_id] = schedule_data
            return MockResponse(200, {
                "status": "success",
                "message": "Schedule updated successfully"
            })
        
        # Record telemetry
        elif url == "/telemetry":
            # Check for auth token for telemetry endpoint
            if 'Authorization' not in headers:
                return MockResponse(401, {"detail": "Not authenticated"})
                
            data = kwargs.get('json', {})
            device_id = data.get('device_id', '')
            energy_usage = data.get('energy_usage')
            
            if not device_id or energy_usage is None:
                return MockResponse(422, {"detail": "Validation error"})
            
            self.telemetry.append(data)
            return MockResponse(201, {
                "status": "success",
                "data": data
            })
        
        return MockResponse(404, {"detail": "Not found"})
    
    def get(self, url, **kwargs):
        headers = kwargs.get('headers', {})
        
        if 'Authorization' not in headers:
            return MockResponse(401, {"detail": "Not authenticated"})
        
        # Get device schedule
        if url.startswith("/devices/") and url.endswith("/schedule"):
            device_id = url.split("/")[2]
            
            if device_id not in self.devices:
                return MockResponse(404, {"detail": "Device not found"})
            
            schedule = self.schedules.get(device_id, [])
            formatted_schedule = []
            
            for i, block in enumerate(schedule):
                formatted_schedule.append({
                    "day_of_week": block.get("day_of_week", i),
                    "start_hour": block.get("start_hour", 9),
                    "end_hour": block.get("end_hour", 17),
                    "power_consumption": block.get("power_consumption", 1.0)
                })
            
            return MockResponse(200, {
                "status": "success",
                "data": {"schedule": formatted_schedule}
            })
        
        return MockResponse(404, {"detail": "Not found"})
    
    def delete(self, url, **kwargs):
        headers = kwargs.get('headers', {})
        
        if 'Authorization' not in headers:
            return MockResponse(401, {"detail": "Not authenticated"})
        
        # Delete device
        if url.startswith("/devices/"):
            device_id = url.split("/")[2]
            
            if device_id in self.devices:
                del self.devices[device_id]
                if device_id in self.schedules:
                    del self.schedules[device_id]
                return MockResponse(200, {
                    "status": "success",
                    "message": "Device deleted successfully"
                })
            else:
                return MockResponse(404, {"detail": "Device not found"})
        
        return MockResponse(404, {"detail": "Not found"})

class TestDeviceManagement:
    def test_create_device_success(self):
        """Device creation should work with valid data"""
        client = MockTestClient()
        
        response = client.post("/devices", 
            headers={"Authorization": "Bearer fake_token"},
            json={
                "name": "Test Device",
                "type": "appliance",
                "room": "living_room",
                "power_rating": 1.5
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data["data"]
        assert data["data"]["name"] == "Test Device"
    
    def test_create_device_invalid_data(self):
        """Device creation should fail with invalid data"""
        client = MockTestClient()
        
        response = client.post("/devices",
            headers={"Authorization": "Bearer fake_token"},
            json={
                "name": "",  # Empty name should fail
                "type": "appliance",
                "room": "living_room",
                "power_rating": 1.5
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_device_unauthorized(self):
        """Device creation should fail without auth token"""
        client = MockTestClient()
        
        response = client.post("/devices", json={
            "name": "Test Device",
            "type": "appliance",
            "room": "living_room",
            "power_rating": 1.5
        })
        
        assert response.status_code == 401
    
    def test_set_device_schedule(self):
        """Setting device schedule should work"""
        client = MockTestClient()
        
        # First create a device
        create_response = client.post("/devices", 
            headers={"Authorization": "Bearer fake_token"},
            json={
                "name": "Test Device",
                "type": "appliance",
                "room": "living_room",
                "power_rating": 1.5
            }
        )
        device_id = create_response.json()["data"]["id"]
        
        schedule = [
            {
                "day_of_week": 1,
                "start_hour": 9,
                "end_hour": 17,
                "power_consumption": 2.0
            }
        ]
        
        response = client.post(f"/devices/{device_id}/schedule",
            headers={"Authorization": "Bearer fake_token"},
            json=schedule
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_device_schedule(self):
        """Getting device schedule should return correct data"""
        client = MockTestClient()
        
        # Create device and set schedule
        create_response = client.post("/devices", 
            headers={"Authorization": "Bearer fake_token"},
            json={"name": "Test Device", "type": "appliance", "room": "living_room", "power_rating": 1.5}
        )
        device_id = create_response.json()["data"]["id"]
        
        schedule = [
            {"day_of_week": 1, "start_hour": 9, "end_hour": 17, "power_consumption": 2.0},
            {"day_of_week": 2, "start_hour": 8, "end_hour": 16, "power_consumption": 1.5}
        ]
        
        client.post(f"/devices/{device_id}/schedule",
            headers={"Authorization": "Bearer fake_token"},
            json=schedule
        )
        
        response = client.get(f"/devices/{device_id}/schedule",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["schedule"]) == 2
    
    def test_delete_device(self):
        """Device deletion should work for existing device"""
        client = MockTestClient()
        
        # First create a device
        create_response = client.post("/devices", 
            headers={"Authorization": "Bearer fake_token"},
            json={"name": "Test Device", "type": "appliance", "room": "living_room", "power_rating": 1.5}
        )
        device_id = create_response.json()["data"]["id"]
        
        response = client.delete(f"/devices/{device_id}",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_delete_nonexistent_device(self):
        """Deleting non-existent device should return 404"""
        client = MockTestClient()
        
        response = client.delete("/devices/nonexistent-device-id",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert response.status_code == 404

class TestTelemetryRecording:
    def test_record_telemetry_success(self):
        """Telemetry recording should work with valid data"""
        client = MockTestClient()
        
        response = client.post("/telemetry", 
            headers={"Authorization": "Bearer fake_token"},
            json={
                "device_id": "test-device-id",
                "energy_usage": 2.5
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["energy_usage"] == 2.5
    
    def test_record_telemetry_invalid_data(self):
        """Telemetry recording should fail with invalid data"""
        client = MockTestClient()
        
        response = client.post("/telemetry", 
            headers={"Authorization": "Bearer fake_token"},
            json={
                "device_id": "",  # Empty device ID
                "energy_usage": None  # Invalid energy usage
            }
        )
        
        assert response.status_code == 422
    
    def test_record_telemetry_unauthorized(self):
        """Telemetry recording should require authentication"""
        client = MockTestClient()
        
        response = client.post("/telemetry", json={
            "device_id": "test-device-id",
            "energy_usage": 2.5
        })
        
        assert response.status_code == 401
    
    def test_multiple_telemetry_records(self):
        """Should handle multiple telemetry records"""
        client = MockTestClient()
        
        # Record multiple data points
        for i in range(3):
            response = client.post("/telemetry", 
                headers={"Authorization": "Bearer fake_token"},
                json={
                    "device_id": f"device-{i}",
                    "energy_usage": float(i + 1) * 1.5
                }
            )
            assert response.status_code == 201
        
        # Verify all records were stored
        assert len(client.telemetry) == 3
