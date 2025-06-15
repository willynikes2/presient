#!/usr/bin/env python3
"""
Find Correct API Endpoints for Your Presient Backend
Tests different endpoint patterns to find the right ones
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_login_endpoint():
    """Find the correct login endpoint"""
    backend_url = "http://localhost:8000"
    
    # Test credentials
    credentials = {
        "username": "john_doe",
        "password": "UserPassword123!"
    }
    
    # Common login endpoint patterns
    login_endpoints = [
        "/api/auth/login",
        "/api/auth/token", 
        "/auth/login",
        "/auth/token",
        "/login",
        "/token",
        "/api/login",
        "/api/token"
    ]
    
    logger.info("🔍 Testing login endpoints...")
    
    for endpoint in login_endpoints:
        url = f"{backend_url}{endpoint}"
        
        try:
            # Try form data (OAuth2 standard)
            response = requests.post(url, data=credentials, timeout=5)
            logger.info(f"📍 {endpoint} (form): {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Found working login endpoint: {endpoint} (form data)")
                return endpoint, "form"
            
            # Try JSON data
            response = requests.post(url, json=credentials, timeout=5)
            logger.info(f"📍 {endpoint} (json): {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Found working login endpoint: {endpoint} (json data)")
                return endpoint, "json"
                
        except Exception as e:
            logger.debug(f"❌ {endpoint}: {e}")
    
    logger.error("❌ No working login endpoint found")
    return None, None

def check_existing_users():
    """Check if we can find existing users or get more info"""
    backend_url = "http://localhost:8000"
    
    logger.info("🔍 Checking for existing users...")
    
    # Try to get user info without auth
    test_endpoints = [
        "/api/users",
        "/api/auth/users", 
        "/users",
        "/api/profiles",
        "/profiles"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            logger.info(f"📍 {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {endpoint} returned data: {len(data) if isinstance(data, list) else 'object'}")
            elif response.status_code == 401:
                logger.info(f"🔐 {endpoint} requires authentication")
            
        except Exception as e:
            logger.debug(f"❌ {endpoint}: {e}")

def test_with_existing_user():
    """Try to use an existing user that might already be in the system"""
    backend_url = "http://localhost:8000"
    
    logger.info("🧪 Testing with potential existing users...")
    
    # Common test users that might exist
    test_users = [
        {"username": "admin", "password": "admin"},
        {"username": "test", "password": "test"},
        {"username": "user", "password": "password"},
        {"username": "sensor_integration", "password": "sensor_password_123"},
        {"username": "john_doe", "password": "UserPassword123!"}  # The one we just created
    ]
    
    login_endpoint, data_format = find_login_endpoint()
    
    if not login_endpoint:
        logger.error("❌ No login endpoint found")
        return None
    
    for user_creds in test_users:
        try:
            url = f"{backend_url}{login_endpoint}"
            
            if data_format == "form":
                response = requests.post(url, data=user_creds, timeout=5)
            else:
                response = requests.post(url, json=user_creds, timeout=5)
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                logger.info(f"✅ Successful login: {user_creds['username']}")
                logger.info(f"🔑 Token: {token[:20]}..." if token else "🔑 No access_token in response")
                return user_creds, token
            else:
                logger.info(f"❌ {user_creds['username']}: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"❌ {user_creds['username']}: {e}")
    
    return None, None

def test_profiles_with_token(user_creds, token):
    """Test accessing profiles with the token"""
    backend_url = "http://localhost:8000"
    
    if not token:
        logger.error("❌ No token available")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test profile endpoints
    profile_endpoints = [
        "/api/profiles",
        "/profiles",
        "/api/profiles/me",
        "/profiles/me"
    ]
    
    logger.info("🧪 Testing profile endpoints with token...")
    
    for endpoint in profile_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", headers=headers, timeout=5)
            logger.info(f"📍 {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"✅ {endpoint} returned {len(data)} profiles")
                    for i, profile in enumerate(data[:3]):  # Show first 3
                        name = profile.get("name", "Unknown")
                        baseline = profile.get("heart_rate_baseline", "N/A")
                        logger.info(f"   📋 Profile {i+1}: {name} (HR: {baseline})")
                else:
                    logger.info(f"✅ {endpoint} returned profile data")
                return True
                
        except Exception as e:
            logger.debug(f"❌ {endpoint}: {e}")
    
    return False

def create_profile_with_correct_endpoint(user_creds, token):
    """Create your biometric profile using the correct endpoints"""
    backend_url = "http://localhost:8000"
    
    if not token:
        logger.error("❌ No token for profile creation")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Your real heart rate data
    profile_data = {
        "name": "John Real Biometric",
        "heart_rate_baseline": 92.75,    # Your baseline
        "heart_rate_range": [80, 104],   # Your full range  
        "heart_rate_stdev": 8.5,         # Your standard deviation
        "biometric_confidence_threshold": 0.75,
        "enrollment_source": "real_mr60bha2_data_80_104_bpm"
    }
    
    # Try different profile creation endpoints
    profile_endpoints = [
        "/api/profiles",
        "/profiles"
    ]
    
    logger.info("📋 Creating your biometric profile...")
    
    for endpoint in profile_endpoints:
        try:
            response = requests.post(
                f"{backend_url}{endpoint}",
                json=profile_data,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📍 {endpoint}: {response.status_code}")
            
            if response.status_code == 201:
                logger.info(f"✅ Profile created successfully!")
                logger.info(f"💓 Your biometric signature: 80-104 BPM range")
                return True
            elif response.status_code != 404:
                logger.error(f"❌ Profile creation failed: {response.text}")
                
        except Exception as e:
            logger.debug(f"❌ {endpoint}: {e}")
    
    return False

def main():
    """Main discovery and setup function"""
    logger.info("🎯 Presient API Endpoint Discovery & Profile Setup")
    logger.info("=" * 60)
    
    # Step 1: Find login endpoint
    logger.info("🔍 Step 1: Finding login endpoint...")
    login_endpoint, data_format = find_login_endpoint()
    
    # Step 2: Check existing setup
    logger.info("\n🔍 Step 2: Checking existing users/profiles...")
    check_existing_users()
    
    # Step 3: Test authentication
    logger.info("\n🔐 Step 3: Testing authentication...")
    user_creds, token = test_with_existing_user()
    
    if not token:
        logger.error("❌ Could not authenticate with any user")
        logger.info("💡 Try checking the API docs at: http://localhost:8000/docs")
        return
    
    # Step 4: Test profiles
    logger.info(f"\n📋 Step 4: Testing profiles with user: {user_creds['username']}")
    profile_access = test_profiles_with_token(user_creds, token)
    
    if not profile_access:
        logger.error("❌ Could not access profiles")
        return
    
    # Step 5: Create your biometric profile
    logger.info("\n🎯 Step 5: Creating your real biometric profile...")
    profile_created = create_profile_with_correct_endpoint(user_creds, token)
    
    # Results
    logger.info("\n📊 Discovery Results:")
    logger.info(f"   Login Endpoint: {login_endpoint} ({data_format})")
    logger.info(f"   Authentication: {'✅' if token else '❌'}")
    logger.info(f"   Profile Access: {'✅' if profile_access else '❌'}")
    logger.info(f"   Profile Created: {'✅' if profile_created else '❌'}")
    
    if token and profile_access and profile_created:
        logger.info("\n🎉 SUCCESS! Your real biometric profile is ready!")
        logger.info("🎯 Your heart rate range (80-104 BPM) is now your biometric signature!")
        logger.info("\n📍 Test with your sensor:")
        logger.info("   Walk near your MR60BHA2 sensor")
        logger.info("   Expected: Ring-style notifications when detected!")
        
        logger.info(f"\n🔧 Working credentials:")
        logger.info(f"   Username: {user_creds['username']}")
        logger.info(f"   Password: {user_creds['password']}")
        logger.info(f"   Login endpoint: {login_endpoint}")
    else:
        logger.error("\n❌ Setup incomplete")
        logger.info("💡 Check the API docs for correct endpoints: http://localhost:8000/docs")

if __name__ == "__main__":
    main()