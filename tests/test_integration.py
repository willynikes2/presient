"""Integration tests for PresientDB"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import uuid

client = TestClient(app)

class TestFullWorkflow:
    """Test complete user workflows"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for tests"""
        # Create unique user for this test run
        username = f"test_{uuid.uuid4().hex[:8]}"
        user_data = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
        
        # Register
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        token = response.json()["access_token"]
        
        return {"Authorization": f"Bearer {token}"}, username
    
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
        assert event["confidence"] == 0.95
        
        # 6. List presence events
        response = client.get("/api/presence/events?limit=5", headers=headers)
        assert response.status_code == 200
        events_data = response.json()
        assert "events" in events_data
        assert events_data["count"] > 0
        
        # 7. Get presence status
        response = client.get(f"/api/presence/status/{username}", headers=headers)
        assert response.status_code == 200
        status = response.json()
        assert status["user_id"] == username
        assert status["status"] in ["online", "offline"]

    def test_validation_errors(self):
        """Test that validation works properly"""
        # Invalid email
        invalid_user = {
            "username": "invalidtest",
            "email": "not-an-email",
            "password": "Test123!",
            "full_name": "Test"
        }
        response = client.post("/api/auth/register", json=invalid_user)
        assert response.status_code == 422
        
        # Weak password
        weak_password = {
            "username": "weakpass",
            "email": "weak@test.com",
            "password": "weak",
            "full_name": "Test"
        }
        response = client.post("/api/auth/register", json=weak_password)
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
