#!/usr/bin/env python3
"""
Fixed Profile Creator for Your Presient API
Matches your actual backend validation requirements
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_your_real_profile():
    """Create biometric profile matching your API requirements"""
    
    backend_url = "http://localhost:8000"
    
    # YOUR REAL HEART RATE DATA
    your_hr_data = {
        "resting_range": [80, 84],      # Current: 80-84 BPM
        "active_range": [103, 104],     # Previous: 103-104 BPM  
        "full_range": [80, 104],        # Complete range
        "overall_baseline": 92.75,      # Middle of your range
        "stdev": 8.5                    # Standard deviation
    }
    
    logger.info("👤 Creating YOUR real biometric profile...")
    logger.info(f"💓 Resting HR: {your_hr_data['resting_range']} BPM")
    logger.info(f"🏃 Active HR: {your_hr_data['active_range']} BPM") 
    logger.info(f"📊 Full Range: {your_hr_data['full_range']} BPM")
    logger.info(f"🎯 Baseline: {your_hr_data['overall_baseline']} BPM")
    
    # Step 1: Register user with correct format (email + strong password)
    auth_data = {
        "username": "john_doe",
        "email": "john@presient.com",  # Required by your API
        "password": "UserPassword123!"  # Strong password with uppercase
    }
    
    try:
        logger.info("📝 Registering user with email and strong password...")
        register_response = requests.post(
            f"{backend_url}/api/auth/register",
            json=auth_data,
            timeout=10
        )
        
        if register_response.status_code == 201:
            logger.info("✅ New user registered successfully")
        elif register_response.status_code == 400:
            logger.info("ℹ️ User already exists - continuing")
        else:
            logger.error(f"❌ Registration error: {register_response.status_code}")
            logger.error(f"Response: {register_response.text}")
            # Continue anyway - user might already exist
            
    except Exception as e:
        logger.error(f"❌ Registration exception: {e}")
        # Continue anyway - user might already exist
    
    # Step 2: Login with correct credentials
    login_data = {
        "username": "john_doe",
        "password": "UserPassword123!"
    }
    
    try:
        logger.info("🔐 Logging in...")
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            data=login_data,  # Form data for OAuth2
            timeout=10
        )
        
        if login_response.status_code == 200:
            auth_token = login_response.json()["access_token"]
            logger.info("✅ Login successful")
        else:
            logger.error(f"❌ Login failed: {login_response.status_code}")
            logger.error(f"Response: {login_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Login exception: {e}")
        return False
    
    # Step 3: Create biometric profile
    profile_data = {
        "name": "John",
        "heart_rate_baseline": your_hr_data["overall_baseline"],
        "heart_rate_range": your_hr_data["full_range"], 
        "heart_rate_stdev": your_hr_data["stdev"],
        "biometric_confidence_threshold": 0.75,  # Lower threshold for wider range
        "enrollment_date": datetime.now().isoformat(),
        "sample_count": 66,  # Total samples from both tests
        "enrollment_source": "real_mr60bha2_multi_state"
    }
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("📋 Creating biometric profile...")
        profile_response = requests.post(
            f"{backend_url}/api/profiles",
            json=profile_data,
            headers=headers,
            timeout=10
        )
        
        if profile_response.status_code == 201:
            logger.info("✅ YOUR biometric profile created!")
            logger.info(f"💓 Baseline: {profile_data['heart_rate_baseline']} BPM")
            logger.info(f"📊 Range: {profile_data['heart_rate_range'][0]}-{profile_data['heart_rate_range'][1]} BPM")
            return True
        else:
            logger.error(f"❌ Profile creation failed: {profile_response.status_code}")
            logger.error(f"Response: {profile_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Profile creation exception: {e}")
        return False

def test_profile_works():
    """Test that the profile loads correctly"""
    backend_url = "http://localhost:8000"
    
    login_data = {
        "username": "john_doe", 
        "password": "UserPassword123!"
    }
    
    try:
        # Login
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            data=login_data,
            timeout=10
        )
        
        if login_response.status_code != 200:
            logger.error(f"❌ Test login failed: {login_response.status_code}")
            return False
        
        auth_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get profiles
        logger.info("🧪 Testing profile loading...")
        profile_response = requests.get(
            f"{backend_url}/api/profiles",
            headers=headers,
            timeout=10
        )
        
        if profile_response.status_code == 200:
            profiles = profile_response.json()
            logger.info(f"✅ Profile test successful - found {len(profiles)} profiles")
            
            for profile in profiles:
                name = profile.get("name", "Unknown")
                baseline = profile.get("heart_rate_baseline", 0)
                hr_range = profile.get("heart_rate_range", [0, 0])
                logger.info(f"📋 {name}: {baseline} BPM (range: {hr_range[0]}-{hr_range[1]} BPM)")
            
            return True
        else:
            logger.error(f"❌ Profile fetch failed: {profile_response.status_code}")
            logger.error(f"Response: {profile_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Profile test exception: {e}")
        return False

def test_detection():
    """Test detection with your heart rate"""
    backend_url = "http://localhost:8000"
    
    login_data = {
        "username": "john_doe",
        "password": "UserPassword123!"
    }
    
    try:
        # Login
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            data=login_data,
            timeout=10
        )
        
        if login_response.status_code != 200:
            logger.error("❌ Could not authenticate for detection test")
            return False
        
        auth_token = login_response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test with your current heart rate (82 BPM from your test)
        logger.info("🎯 Testing detection with your current heart rate...")
        
        event_data = {
            "sensor_id": "presient-sensor-1",
            "heart_rate": 82.0,  # Your current resting HR
            "breathing_rate": 15.0,
            "confidence": 0.90,
            "source": "real_biometric_test",
            "timestamp": datetime.now().isoformat()
        }
        
        detection_response = requests.post(
            f"{backend_url}/api/presence/event",
            json=event_data,
            headers=headers,
            timeout=10
        )
        
        if detection_response.status_code == 201:
            result = detection_response.json()
            logger.info(f"✅ Detection successful!")
            logger.info(f"🎯 Event ID: {result.get('id', 'unknown')}")
            logger.info(f"💓 Heart Rate: 82.0 BPM")
            logger.info(f"📊 Confidence: {result.get('confidence', 0):.1%}")
            logger.info("📱 This should trigger Ring-style notifications!")
            return True
        else:
            logger.error(f"❌ Detection failed: {detection_response.status_code}")
            logger.error(f"Response: {detection_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Detection test exception: {e}")
        return False

def check_api_structure():
    """Check what API endpoints are available"""
    backend_url = "http://localhost:8000"
    
    try:
        logger.info("🔍 Checking API structure...")
        
        # Check if docs are available
        docs_response = requests.get(f"{backend_url}/docs", timeout=5)
        if docs_response.status_code == 200:
            logger.info("📖 API docs available at: http://localhost:8000/docs")
        
        # Check health endpoint
        health_response = requests.get(f"{backend_url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            logger.info(f"✅ Backend health: {health_data}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API check failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🎯 Fixed Profile Creator for Your Presient API")
    logger.info("Using your real heart rate data: 80-104 BPM")
    logger.info("=" * 60)
    
    # Step 0: Check API structure
    logger.info("🔍 Step 0: Checking API...")
    api_ok = check_api_structure()
    
    if not api_ok:
        logger.error("❌ API check failed")
        return
    
    # Step 1: Create profile
    logger.info("\n👤 Step 1: Creating biometric profile...")
    profile_created = create_your_real_profile()
    
    if not profile_created:
        logger.error("❌ Profile creation failed")
        return
    
    # Step 2: Test profile loading  
    logger.info("\n🧪 Step 2: Testing profile loading...")
    profile_works = test_profile_works()
    
    if not profile_works:
        logger.error("❌ Profile test failed")
        return
    
    # Step 3: Test detection
    logger.info("\n🎯 Step 3: Testing detection...")
    detection_works = test_detection()
    
    # Results
    logger.info("\n📊 Results:")
    logger.info(f"   API Check: {'✅' if api_ok else '❌'}")
    logger.info(f"   Profile Creation: {'✅' if profile_created else '❌'}")
    logger.info(f"   Profile Loading: {'✅' if profile_works else '❌'}")
    logger.info(f"   Detection Test: {'✅' if detection_works else '❌'}")
    
    if api_ok and profile_created and profile_works and detection_works:
        logger.info("\n🎉 SUCCESS! Your real biometric profile is ready!")
        logger.info("🎯 Your heart rate patterns (80-104 BPM) are now your biometric signature!")
        logger.info("\n📍 Now test with your actual sensor:")
        logger.info("   Walk near your MR60BHA2 sensor")
        logger.info("   Expected: High confidence match when HR = 80-104 BPM") 
        logger.info("   Expected: Ring-style notifications!")
        logger.info("\n🔧 Next: Run test_real_authentication.py")
    else:
        logger.error("\n❌ Setup failed - check errors above")
        logger.info("\n🔧 Try checking the API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()