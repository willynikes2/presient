#!/usr/bin/env python3
"""
Test real biometric authentication
"""

import asyncio
import logging
import paho.mqtt.client as mqtt
import requests
from datetime import datetime
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationTester:
    """Test real biometric authentication"""
    
    def __init__(self):
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.backend_url = "http://localhost:8000"
        self.test_samples = []
        
    def test_mqtt_connection(self):
        """Test MQTT connection and sensor data"""
        logger.info("🧪 Testing MQTT connection...")
        
        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload = msg.payload.decode('utf-8')
                
                if "heart_rate" in topic:
                    hr = float(payload)
                    self.test_samples.append(hr)
                    logger.info(f"💓 Received HR: {hr} BPM")
                    
            except:
                pass
        
        client = mqtt.Client(client_id="presient_tester")
        client.on_message = on_message
        client.connect(self.mqtt_host, self.mqtt_port, 60)
        client.subscribe("presient/sensor1/heart_rate/state")
        client.subscribe("presient/sensor1/sensor/presient_mr60bha2_sensor_heart_rate/state")
        client.loop_start()
        
        logger.info("📡 Listening for 10 seconds...")
        import time
        time.sleep(10)
        
        client.loop_stop()
        client.disconnect()
        
        if self.test_samples:
            avg_hr = statistics.mean(self.test_samples)
            logger.info(f"✅ MQTT working - Average HR: {avg_hr:.1f} BPM")
            return True
        else:
            logger.error("❌ No MQTT data received")
            return False
    
    def test_backend_connection(self):
        """Test backend API connection"""
        logger.info("🧪 Testing backend connection...")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend is responding")
                return True
            else:
                logger.error(f"❌ Backend error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Backend connection failed: {e}")
            return False
    
    def test_profiles_loaded(self):
        """Test if biometric profiles are loaded"""
        logger.info("🧪 Testing biometric profiles...")
        
        try:
            # Try to authenticate first
            auth_data = {
                "username": "john_doe",  # Default test user
                "password": "user_password_123"
            }
            
            login_response = requests.post(
                f"{self.backend_url}/api/auth/login",
                data=auth_data,
                timeout=10
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Get profiles
                profile_response = requests.get(
                    f"{self.backend_url}/api/profiles",
                    headers=headers,
                    timeout=10
                )
                
                if profile_response.status_code == 200:
                    profiles = profile_response.json()
                    logger.info(f"✅ Found {len(profiles)} biometric profiles")
                    
                    for profile in profiles:
                        name = profile.get("name", "Unknown")
                        baseline = profile.get("heart_rate_baseline", 0)
                        logger.info(f"📋 Profile: {name} (baseline: {baseline:.1f} BPM)")
                    
                    return len(profiles) > 0
                else:
                    logger.error(f"❌ Profiles request failed: {profile_response.status_code}")
                    return False
            else:
                logger.error(f"❌ Authentication failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Profile test error: {e}")
            return False
    
    async def run_full_test(self):
        """Run complete authentication test"""
        logger.info("🎯 Real Biometric Authentication Test")
        logger.info("=" * 50)
        
        # Test 1: MQTT
        mqtt_ok = self.test_mqtt_connection()
        
        # Test 2: Backend  
        backend_ok = self.test_backend_connection()
        
        # Test 3: Profiles
        profiles_ok = self.test_profiles_loaded()
        
        # Results
        logger.info("\n📊 Test Results:")
        logger.info(f"   MQTT Connection: {'✅' if mqtt_ok else '❌'}")
        logger.info(f"   Backend API: {'✅' if backend_ok else '❌'}")
        logger.info(f"   Biometric Profiles: {'✅' if profiles_ok else '❌'}")
        
        if mqtt_ok and backend_ok and profiles_ok:
            logger.info("\n🎉 All tests passed!")
            logger.info("🎯 Your real biometric authentication is ready!")
            logger.info("\n📍 Walk near your MR60BHA2 sensor to trigger detection")
        else:
            logger.error("\n❌ Some tests failed - check setup")
        
        return mqtt_ok and backend_ok and profiles_ok

async def main():
    tester = AuthenticationTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
