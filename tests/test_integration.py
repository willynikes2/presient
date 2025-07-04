import json
import uuid
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

from backend.main import app

client = TestClient(app)


class TestFullWorkflow:
    @pytest.fixture
    def auth_headers(self):
        """Create a test user and return auth headers"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:8]
        username = f"test_{random_suffix}"
        
        # Register user
        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "TestPass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        
        # Get token
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        return headers, username
    
    def test_complete_workflow(self, auth_headers):
        """Test complete user workflow"""
        headers, username = auth_headers
        
        # 1. Get user info
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["username"] == username
        
        # 2. Get/create profile
        response = client.get("/api/profiles/me", headers=headers)
        assert response.status_code == 200
        profile = response.json()
        
        # 3. Update profile
        update_data = {
            "bio": "Integration test bio",
            "location": "Test Location"
        }
        response = client.put("/api/profiles/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        # 4. Update preferences
        pref_data = {
            "theme": "dark",
            "language": "en-US", 
            "timezone": "UTC",
            "notifications": {"email": True, "push": False, "sms": False, "in_app": True}
        }
        response = client.put("/api/profiles/me/preferences", json=pref_data, headers=headers)
        assert response.status_code == 200
        
        # 5. Create presence event
        event_data = {
            "user_id": username,
            "sensor_id": "test-sensor-01",
            "confidence": 0.95
        }
        response = client.post("/api/presence/event", json=event_data, headers=headers)
        assert response.status_code == 201
        event = response.json()
        print("EVENT RESPONSE:", event)
        
        # Handle potential string response
        if isinstance(event, str):
            event = json.loads(event)
            
        assert event["confidence"] == 0.95
        assert event["user_id"] == username
        assert event["sensor_id"] == "test-sensor-01"
        
        # 6. Get presence events
        response = client.get("/api/presence/events", headers=headers)
        assert response.status_code == 200
        events_data = response.json()
        assert events_data["count"] >= 1
        
        # 7. Get user presence status
        response = client.get(f"/api/presence/status/{username}", headers=headers)
        assert response.status_code == 200
    
    def test_validation_errors(self):
        """Test validation error handling"""
        # Test registration with invalid data
        response = client.post(
            "/api/auth/register",
            json={
                "username": "a",  # Too short
                "email": "invalid-email",
                "password": "weak",
                "full_name": ""
            }
        )
        assert response.status_code == 422
        
        # Test presence event with invalid confidence
        headers = {"Authorization": "Bearer fake-token"}
        response = client.post(
            "/api/presence/event",
            json={
                "user_id": "test",
                "sensor_id": "test",
                "confidence": 1.5  # > 1.0
            },
            headers=headers
        )
        assert response.status_code in [401, 422]  # Either auth fails or validation fails
