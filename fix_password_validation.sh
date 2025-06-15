#!/bin/bash

echo "🔧 Fixing password validation in test files..."

# Fix test_integration.py to use valid passwords
echo -e "\n📝 Updating test_integration.py with proper password format..."
cat > tests/test_integration.py << 'EOF'
import json
import uuid
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

from backend.main import app

client = TestClient(app)

def test_complete_user_flow():
    """Test complete user flow: register -> login -> create profile -> presence event"""
    
    # Generate unique username for this test
    unique_username = f"test_{uuid.uuid4().hex[:8]}"
    
    # 1. Register user (password must have uppercase letter)
    register_data = {
        "username": unique_username,
        "email": f"{unique_username}@test.com",
        "password": "TestPass123"  # Changed to include uppercase
    }
    
    register_response = client.post("/api/auth/register", json=register_data)
    assert register_response.status_code == 201
    
    # 2. Login
    login_data = {
        "username": unique_username,
        "password": "TestPass123"  # Changed to match registration
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get user profile
    profile_response = client.get("/api/profiles/me", headers=headers)
    assert profile_response.status_code == 200
    
    # 4. Create presence event
    presence_data = {
        "user_id": unique_username,
        "sensor_id": "test-sensor-01",
        "confidence": 0.95,
        "timestamp": datetime.now().isoformat()
    }
    
    presence_response = client.post("/api/presence/event", json=presence_data, headers=headers)
    assert presence_response.status_code == 201
    
    # Parse response
    response_data = presence_response.json()
    if isinstance(response_data, str):
        response_data = json.loads(response_data)
    
    assert "id" in response_data
    assert response_data["user_id"] == unique_username
    assert response_data["sensor_id"] == "test-sensor-01"
    assert response_data["confidence"] == 0.95
    
    # 5. Get presence events
    events_response = client.get("/api/presence/events", headers=headers)
    assert events_response.status_code == 200
    
    events_data = events_response.json()
    assert len(events_data) >= 1
    
    # 6. Get presence status
    status_response = client.get(f"/api/presence/status/{unique_username}", headers=headers)
    # Accept both 200 (user found) and 404 (no presence data) as valid responses
    assert status_response.status_code in [200, 404]

def test_presence_event_creation():
    """Test standalone presence event creation"""
    
    # Generate unique username for this test
    unique_username = f"test_{uuid.uuid4().hex[:8]}"
    
    # Register and login first
    register_data = {
        "username": unique_username,
        "email": f"{unique_username}@test.com",
        "password": "TestPass123"  # Changed to include uppercase
    }
    
    register_response = client.post("/api/auth/register", json=register_data)
    assert register_response.status_code == 201
    
    login_data = {
        "username": unique_username,
        "password": "TestPass123"  # Changed to match registration
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create presence event
    presence_data = {
        "user_id": unique_username,
        "sensor_id": "test-sensor-02",
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/api/presence/event", json=presence_data, headers=headers)
    assert response.status_code == 201
    
    # Parse response
    response_data = response.json()
    if isinstance(response_data, str):
        response_data = json.loads(response_data)
    
    assert "id" in response_data
    assert response_data["user_id"] == unique_username
    assert response_data["sensor_id"] == "test-sensor-02"
    assert response_data["confidence"] == 0.85
EOF

echo "✅ Fixed test_integration.py passwords"

# Also check and fix any other test files that might have password issues
echo -e "\n🔍 Checking other test files for password validation issues..."

# Check test_routes.py
if grep -q "testpass123" tests/test_routes.py; then
    echo "📝 Fixing passwords in test_routes.py..."
    sed -i 's/testpass123/TestPass123/g' tests/test_routes.py
    echo "✅ Fixed test_routes.py passwords"
fi

# Check any other test files
find tests/ -name "*.py" -exec grep -l "testpass123" {} \; | while read file; do
    echo "📝 Fixing passwords in $file..."
    sed -i 's/testpass123/TestPass123/g' "$file"
    echo "✅ Fixed passwords in $file"
done

echo -e "\n🎯 Password validation fixes complete!"
echo "The password 'TestPass123' meets all requirements:"
echo "  ✅ At least 8 characters"
echo "  ✅ Contains uppercase letter (T, P)"
echo "  ✅ Contains lowercase letters"
echo "  ✅ Contains numbers"
echo ""
echo "Now run: pytest tests/ -v"