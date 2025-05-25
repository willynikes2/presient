"""Basic tests for PresientDB routes"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data

def test_register_user():
    user_data = {
        "username": "testuser123",
        "email": "test123@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    response = client.post("/api/auth/register", json=user_data)
    # Either 201 (created) or 409 (already exists)
    assert response.status_code in [201, 409]

def test_login():
    # Ensure user exists first
    user_data = {
        "username": "logintest",
        "email": "logintest@example.com",
        "password": "LoginTest123!",
        "full_name": "Login Test"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Test login
    response = client.post(
        "/api/auth/token",
        data={"username": "logintest", "password": "LoginTest123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_protected_route_without_auth():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_mqtt_status():
    response = client.get("/api/mqtt/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "connected" in data
