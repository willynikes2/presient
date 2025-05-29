#!/usr/bin/env python3
"""
Debug the presence event response
"""
import requests
import json

# Quick test of the presence endpoint
BASE_URL = "http://localhost:8000"

# First, get a token
register_data = {
    "username": "debug_user_123",
    "email": "debug@test.com",
    "password": "TestPass123",
    "full_name": "Debug User"
}

response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
if response.status_code == 201:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test presence event
    event_data = {
        "user_id": "debug_user_123",
        "sensor_id": "test-sensor-01",
        "confidence": 0.95
    }
    
    response = requests.post(f"{BASE_URL}/api/presence/event", json=event_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Raw content: {response.content}")
    print(f"Response text: {response.text}")
    
    # Try to parse
    try:
        data = response.json()
        print(f"\nParsed JSON type: {type(data)}")
        print(f"Parsed JSON: {data}")
        
        if isinstance(data, str):
            print("\n⚠️  Response is a string, trying to parse again...")
            data = json.loads(data)
            print(f"Double-parsed type: {type(data)}")
            print(f"Double-parsed: {data}")
    except Exception as e:
        print(f"\nError parsing JSON: {e}")
else:
    print(f"Registration failed: {response.status_code}")
