#!/usr/bin/env python3
"""
Diagnose and fix 500 errors in the API
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

def check_database_schema():
    """Check database schema for issues"""
    print("\n🔍 Checking database schema...")
    
    db_path = "backend/db/dev.db"
    if not os.path.exists(db_path):
        db_path = "presient.db"
    
    if not os.path.exists(db_path):
        print("❌ No database found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"✓ Found tables: {tables}")
    
    # Check users table schema
    if "users" in tables:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n📊 Users table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("❌ Users table not found!")
    
    # Check profiles table schema
    if "profiles" in tables:
        cursor.execute("PRAGMA table_info(profiles)")
        columns = cursor.fetchall()
        print("\n📊 Profiles table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    # Check presence_events table schema
    if "presence_events" in tables:
        cursor.execute("PRAGMA table_info(presence_events)")
        columns = cursor.fetchall()
        print("\n📊 Presence_events table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    return True

def test_with_details():
    """Test endpoints and capture detailed error information"""
    print("\n🧪 Testing endpoints with detailed error capture...\n")
    
    # First, register a user
    timestamp = int(datetime.now().timestamp())
    username = f"debug_user_{timestamp}"
    
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPassword123",
        "full_name": "Debug User"
    }
    
    print("1️⃣ Testing Registration...")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 201:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    auth_data = response.json()
    token = auth_data.get("access_token")
    user_id = auth_data.get("user_id")
    print(f"   ✓ Token received: {token[:30]}...")
    print(f"   ✓ User ID: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test profile endpoint
    print("\n2️⃣ Testing GET /api/profiles/me...")
    response = requests.get(f"{BASE_URL}/api/profiles/me", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 500:
        print(f"   ❌ Server Error: {response.text}")
        # Try to get more details
        error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
        if "detail" in error_data:
            print(f"   Error details: {json.dumps(error_data['detail'], indent=2)}")
    elif response.status_code == 200:
        print(f"   ✓ Profile retrieved successfully")
        profile = response.json()
        print(f"   Profile ID: {profile.get('id')}")
    
    # Test presence event creation
    print("\n3️⃣ Testing POST /api/presence/event...")
    event_data = {
        "user_id": user_id,
        "sensor_id": "debug-sensor-001",
        "confidence": 0.85
    }
    
    response = requests.post(f"{BASE_URL}/api/presence/event", json=event_data, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 500:
        print(f"   ❌ Server Error: {response.text}")
        error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
        if "detail" in error_data:
            print(f"   Error details: {json.dumps(error_data['detail'], indent=2)}")
    elif response.status_code == 200:
        print(f"   ✓ Event created successfully")

def check_model_issues():
    """Check for common model issues"""
    print("\n🔍 Checking for model issues...")
    
    # Check if models have proper UUID handling
    print("\n📋 Checking model definitions...")
    
    # Check profile.py for UUID issues
    try:
        with open("backend/models/profile.py", "r") as f:
            profile_content = f.read()
            
        if "import uuid" in profile_content:
            print("✓ Profile model imports uuid")
        else:
            print("⚠️  Profile model doesn't import uuid")
            
        if "default=uuid.uuid4" in profile_content or "default=lambda: str(uuid.uuid4())" in profile_content:
            print("✓ Profile model has UUID default")
        else:
            print("⚠️  Profile model might not have proper UUID default")
    except Exception as e:
        print(f"❌ Error reading profile model: {e}")
    
    # Check for relationship issues
    if "presence_events" in profile_content:
        print("✓ Profile model has presence_events relationship")
        if "PresenceEvent" in profile_content:
            print("✓ Relationship references PresenceEvent correctly")
        elif "PresenceEvents" in profile_content:
            print("❌ Relationship references PresenceEvents (should be PresenceEvent)")

def create_fix_script():
    """Create a script to fix common issues"""
    print("\n📝 Creating fix script...")
    
    fix_content = '''#!/usr/bin/env python3
"""
Fix common issues causing 500 errors
"""

import os
import re

def fix_profile_model():
    """Fix profile model issues"""
    print("Fixing profile model...")
    
    with open("backend/models/profile.py", "r") as f:
        content = f.read()
    
    # Fix imports
    if "import uuid" not in content:
        content = "import uuid\\n" + content
    
    # Fix UUID defaults
    content = re.sub(
        r'id = Column\\(String, primary_key=True\\)',
        'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
        content
    )
    
    # Fix relationship name
    content = content.replace("PresenceEvents", "PresenceEvent")
    
    with open("backend/models/profile.py", "w") as f:
        f.write(content)
    
    print("✓ Fixed profile model")

def fix_presence_model():
    """Fix presence event model issues"""
    print("Fixing presence event model...")
    
    with open("backend/models/presence_events.py", "r") as f:
        content = f.read()
    
    # Fix imports
    if "import uuid" not in content:
        content = "import uuid\\n" + content
    
    # Fix UUID defaults
    content = re.sub(
        r'id = Column\\(String, primary_key=True\\)',
        'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
        content
    )
    
    with open("backend/models/presence_events.py", "w") as f:
        f.write(content)
    
    print("✓ Fixed presence event model")

def fix_route_issues():
    """Fix route registration issues"""
    print("Fixing route issues...")
    
    # Check main.py for proper route inclusion
    with open("backend/main.py", "r") as f:
        content = f.read()
    
    # Ensure presence routes are included
    if "app.include_router(presence.router)" not in content:
        # Find where routers are included
        router_section = content.find("app.include_router(profiles.router)")
        if router_section != -1:
            # Add presence router after profiles router
            content = content[:router_section] + \\
                     "app.include_router(profiles.router)\\n" + \\
                     "app.include_router(presence.router)\\n" + \\
                     content[router_section + len("app.include_router(profiles.router)"):]
            
            with open("backend/main.py", "w") as f:
                f.write(content)
            print("✓ Added presence router to main.py")
    else:
        print("✓ Presence router already included")

if __name__ == "__main__":
    fix_profile_model()
    fix_presence_model()
    fix_route_issues()
    print("\\n✅ Fixes applied! Please restart your server.")
'''
    
    with open("fix_500_errors.py", "w") as f:
        f.write(fix_content)
    
    print("✓ Created fix_500_errors.py")
    print("\nRun: python fix_500_errors.py")

def main():
    print("🔍 DIAGNOSING 500 ERRORS IN PRESIENT API")
    print("=" * 50)
    
    # Check database schema
    check_database_schema()
    
    # Test endpoints with detailed error capture
    test_with_details()
    
    # Check for model issues
    check_model_issues()
    
    # Create fix script
    create_fix_script()
    
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS COMPLETE")
    print("\nNext steps:")
    print("1. Run: python fix_500_errors.py")
    print("2. Restart your server")
    print("3. Run the tests again")
    print("\nCheck the server terminal for detailed error logs!")

if __name__ == "__main__":
    main()