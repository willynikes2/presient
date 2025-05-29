"""Working integration tests for PresientDB"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import uuid

client = TestClient(app)

def test_auth_flow():
    """Test basic authentication flow"""
    # Create unique user
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
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    
    # Use token to get user info
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["username"] == username

def test_profile_me_endpoint():
    """Test the /me profile endpoint"""
    # Create user and get token
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
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /api/profiles/me
    response = client.get("/api/profiles/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert "id" in profile
    assert "preferences" in profile

def test_presence_event():
    """Test creating presence event"""
    # Get auth token
    username = f"test_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create presence event
    event_data = {
        "user_id": username,
        "sensor_id": "test-sensor-01",
        "confidence": 0.95
    }
    response = client.post("/api/presence/event", json=event_data, headers=headers)
    assert response.status_code == 201

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
