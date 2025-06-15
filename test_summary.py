import subprocess
import requests
import json
from datetime import datetime

print("=" * 60)
print("PRESIENTDB API TEST SUMMARY")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

BASE_URL = "http://localhost:8000"

# 1. Check if server is running
print("\n1. SERVER STATUS")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    health = response.json()
    print(f"   ✓ Server is running")
    print(f"   - Status: {health['status']}")
    print(f"   - Database: {health['checks']['database']}")
    print(f"   - MQTT: {health['checks']['mqtt']}")
except Exception as e:
    print(f"   ✗ Server not responding: {e}")
    exit(1)

# 2. Test authentication
print("\n2. AUTHENTICATION TEST")
timestamp = int(datetime.now().timestamp())
test_user = {
    "username": f"summary_test_{timestamp}",
    "email": f"summary_{timestamp}@test.com",
    "password": "SummaryTest123!",
    "full_name": "Summary Test User"
}

try:
    # Register
    response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
    if response.status_code == 201:
        print("   ✓ User registration: PASSED")
        token = response.json()["access_token"]
        
        # Test auth/me
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            print("   ✓ Token validation: PASSED")
        else:
            print(f"   ✗ Token validation: FAILED ({response.status_code})")
    else:
        print(f"   ✗ User registration: FAILED ({response.status_code})")
        token = None
except Exception as e:
    print(f"   ✗ Authentication test failed: {e}")
    token = None

# 3. Test profile endpoints
if token:
    print("\n3. PROFILE ENDPOINTS TEST")
    try:
        response = requests.get(f"{BASE_URL}/api/profiles/me", headers=headers)
        if response.status_code == 200:
            print("   ✓ GET /api/profiles/me: PASSED")
        else:
            print(f"   ✗ GET /api/profiles/me: FAILED ({response.status_code})")
    except Exception as e:
        print(f"   ✗ Profile test failed: {e}")

# 4. Test presence endpoints
if token:
    print("\n4. PRESENCE ENDPOINTS TEST")
    try:
        event_data = {
            "user_id": test_user["username"],
            "sensor_id": "test-sensor-01",
            "confidence": 0.95
        }
        response = requests.post(f"{BASE_URL}/presence/event", json=event_data, headers=headers)
        if response.status_code == 201:
            print("   ✓ POST /presence/event: PASSED")
        else:
            print(f"   ✗ POST /presence/event: FAILED ({response.status_code})")
            
        # List events
        response = requests.get(f"{BASE_URL}/presence/events?limit=5", headers=headers)
        if response.status_code == 200:
            print("   ✓ GET /presence/events: PASSED")
        else:
            print(f"   ✗ GET /presence/events: FAILED ({response.status_code})")
    except Exception as e:
        print(f"   ✗ Presence test failed: {e}")

# 5. Run pytest
print("\n5. PYTEST RESULTS")
try:
    result = subprocess.run(["pytest", "tests/", "-q"], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ All pytest tests passed")
    else:
        print("   ✗ Some pytest tests failed")
        print(result.stdout[-200:])  # Last 200 chars of output
except Exception as e:
    print(f"   ✗ Could not run pytest: {e}")

print("\n" + "=" * 60)
print("TEST SUMMARY COMPLETE")
print("=" * 60)
