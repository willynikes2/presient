"""
Simple test suite to verify PresientDB is working
Save as: tests/test_routes.py
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json

# Create test client
client = TestClient(app)

# ==================== Basic Health Tests ====================

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data

# ==================== Auth Tests ====================

def test_register_new_user():
    """Test user registration"""
    user_data = {
        "username": "pytest_user",
        "email": "pytest@example.com",
        "password": "PyTest123!",
        "full_name": "PyTest User"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    
    # Should either succeed or fail with duplicate (if test ran before)
    assert response.status_code in [201, 409]
    
    if response.status_code == 201:
        data = response.json()
        assert "access_token" in data
        assert data["status"] == "success"

def test_login():
    """Test user login"""
    # First ensure user exists
    user_data = {
        "username": "pytest_login",
        "email": "pytest_login@example.com",
        "password": "PyTest123!",
        "full_name": "PyTest Login User"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Now test login
    login_data = {
        "username": "pytest_login",
        "password": "PyTest123!"
    }
    
    response = client.post(
        "/api/auth/token",
        data=login_data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route_without_token():
    """Test accessing protected route without token"""
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_protected_route_with_token():
    """Test accessing protected route with valid token"""
    # Register and login
    user_data = {
        "username": "pytest_protected",
        "email": "pytest_protected@example.com",
        "password": "PyTest123!",
        "full_name": "PyTest Protected User"
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    
    if reg_response.status_code == 409:
        # User exists, login instead
        login_response = client.post(
            "/api/auth/token",
            data={"username": user_data["username"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]
    else:
        token = reg_response.json()["access_token"]
    
    # Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["username"] == "pytest_protected"

# ==================== Profile Tests ====================

def test_get_profile_unauthorized():
    """Test getting profile without auth"""
    response = client.get("/api/profiles/me")
    assert response.status_code == 401

def test_profile_operations():
    """Test profile CRUD operations"""
    # Get auth token
    user_data = {
        "username": "pytest_profile",
        "email": "pytest_profile@example.com",
        "password": "PyTest123!",
        "full_name": "PyTest Profile User"
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    
    if reg_response.status_code == 409:
        login_response = client.post(
            "/api/auth/token",
            data={"username": user_data["username"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]
    else:
        token = reg_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get profile (should auto-create)
    response = client.get("/api/profiles/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert "id" in profile
    assert "preferences" in profile
    
    # Update profile
    update_data = {
        "bio": "Testing profile update",
        "location": "Test City"
    }
    response = client.put("/api/profiles/me", json=update_data, headers=headers)
    assert response.status_code == 200
    
    # Update preferences
    pref_data = {
        "theme": "dark",
        "language": "en-US",
        "timezone": "UTC",
        "notifications": {"email": True, "push": False}
    }
    response = client.put("/api/profiles/me/preferences", json=pref_data, headers=headers)
    assert response.status_code == 200

# ==================== Presence Tests ====================

def test_presence_event_unauthorized():
    """Test creating presence event without auth"""
    event_data = {
        "user_id": "test",
        "sensor_id": "sensor-001",
        "confidence": 0.95
    }
    response = client.post("/api/presence/event", json=event_data)
    assert response.status_code == 401

def test_create_presence_event():
    """Test creating a presence event"""
    # Get auth token
    user_data = {
        "username": "pytest_presence",
        "email": "pytest_presence@example.com",
        "password": "PyTest123!",
        "full_name": "PyTest Presence User"
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    
    if reg_response.status_code == 409:
        login_response = client.post(
            "/api/auth/token",
            data={"username": user_data["username"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]
    else:
        token = reg_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create presence event
    event_data = {
        "user_id": "pytest_presence",
        "sensor_id": "sensor-001",
        "confidence": 0.95
    }
    response = client.post("/api/presence/event", json=event_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["confidence"] == 0.95

def test_list_presence_events():
    """Test listing presence events"""
    # Get auth token (reuse from previous test)
    login_response = client.post(
        "/api/auth/token",
        data={"username": "pytest_presence", "password": "PyTest123!"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List events
    response = client.get("/api/presence/events?limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data

# ==================== MQTT Tests ====================

def test_mqtt_status():
    """Test MQTT status endpoint"""
    response = client.get("/api/mqtt/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "connected" in data
    assert "broker" in data

# ==================== Error Handling Tests ====================

def test_invalid_json():
    """Test handling of invalid JSON"""
    response = client.post(
        "/api/auth/register",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422

def test_validation_error():
    """Test validation error handling"""
    # Missing required fields
    response = client.post("/api/auth/register", json={})
    assert response.status_code == 422
    
    # Invalid email
    response = client.post("/api/auth/register", json={
        "username": "test",
        "email": "not-an-email",
        "password": "Test123!",
        "full_name": "Test"
    })
    assert response.status_code == 422

def test_not_found_error():
    """Test 404 error handling"""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404

# ==================== Cleanup ====================

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after tests"""
    yield
    # Cleanup code here if needed

if __name__ == "__main__":
    pytest.main([__file__, "-v"])