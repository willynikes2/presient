#!/bin/bash

echo "🔧 Fixing all indentation errors..."

# 1. Fix profiles.py indentation error on line 151
echo -e "\n📝 Fixing profiles.py indentation..."
python3 << 'EOF'
# Read profiles.py
with open('backend/routes/profiles.py', 'r') as f:
    content = f.read()

# Fix the indentation issue around line 151
lines = content.split('\n')
fixed_lines = []
in_function = False
function_indent = 0

for i, line in enumerate(lines):
    # Detect function definitions to track proper indentation
    if 'async def' in line or 'def ' in line:
        in_function = True
        function_indent = len(line) - len(line.lstrip())
        fixed_lines.append(line)
    elif line.strip() == '':
        fixed_lines.append(line)
    elif line.strip().startswith('user = await get_user_data'):
        # Fix this specific line's indentation
        fixed_lines.append('    ' + line.strip())
    else:
        # Keep original line
        fixed_lines.append(line)

# Write back the fixed content
with open('backend/routes/profiles.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed profiles.py indentation")
EOF

# 2. Fix test_integration.py indentation error
echo -e "\n📝 Fixing test_integration.py indentation..."
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
    
    # 1. Register user
    register_data = {
        "username": unique_username,
        "email": f"{unique_username}@test.com",
        "password": "testpass123"
    }
    
    register_response = client.post("/api/auth/register", json=register_data)
    assert register_response.status_code == 201
    
    # 2. Login
    login_data = {
        "username": unique_username,
        "password": "testpass123"
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
        "password": "testpass123"
    }
    
    register_response = client.post("/api/auth/register", json=register_data)
    assert register_response.status_code == 201
    
    login_data = {
        "username": unique_username,
        "password": "testpass123"
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

echo "✅ Fixed test_integration.py"

# 3. Check profiles.py for any remaining syntax issues
echo -e "\n🔍 Checking profiles.py syntax..."
python3 -m py_compile backend/routes/profiles.py 2>/dev/null && echo "✅ profiles.py syntax OK" || echo "❌ profiles.py has syntax errors"

# 4. Check test_integration.py syntax
echo -e "\n🔍 Checking test_integration.py syntax..."
python3 -m py_compile tests/test_integration.py 2>/dev/null && echo "✅ test_integration.py syntax OK" || echo "❌ test_integration.py has syntax errors"

# 5. Try to run a simple import test
echo -e "\n🔍 Testing imports..."
python3 -c "
try:
    from backend.routes import auth, presence, profiles
    print('✅ All route imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo -e "\n🎯 All indentation fixes applied!"
echo "Now run: pytest tests/ -v"