#!/usr/bin/env python3
"""
Connected Biometric Bridge - Sends Real Push Notifications
Connects biometric matching to backend notification system
"""

import asyncio
import logging
import paho.mqtt.client as mqtt
import requests
import time
import os
import sys
import json
from datetime import datetime
from typing import Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_biometric_matcher import RealBiometricMatcher, BiometricSample

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectedBiometricBridge:
    """Biometric bridge that sends real push notifications via backend"""
    
    def __init__(self):
        self.mqtt_host = "192.168.1.135"
        self.mqtt_port = 1883
        self.backend_url = "http://localhost:8000"  # Fixed to use localhost
        
        # Initialize biometric matcher
        self.matcher = RealBiometricMatcher()
        logger.info(f"✅ Biometric matcher loaded with {len(self.matcher.profiles)} profiles")
        
        # Tracking
        self.last_match_time = None
        self.match_cooldown = 30  # seconds
        self.total_matches = 0
        self.auth_token = None
        
    def send_notification(self, match_result, heart_rate: float):
        """Send notification via /api/presence/event endpoint"""
        try:
            # Use the working /api/presence/event endpoint with correct format
            presence_data = {
                "sensor_id": "presient-sensor-1",
                "user_id": match_result.user_id,  # FIXED: use user_id instead of matched_user_id
                "heart_rate": heart_rate,
                "confidence": match_result.confidence,
                "source": "biometric_bridge",
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            response = requests.post(
                f"{self.backend_url}/api/presence/event",
                json=presence_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info("📱 PUSH NOTIFICATION SENT VIA PRESENCE EVENT!")
                return True
            else:
                logger.error(f"❌ Presence event failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Notification error: {e}")
            return False
    
    def test_backend_connection(self):
        """Test backend connection and available endpoints"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Backend health check passed")
                
                # Check notification system status
                if "notification_system" in health_data.get("checks", {}):
                    logger.info("✅ Backend notification system available")
                
                # Check push tokens
                if "push_tokens" in health_data.get("checks", {}):
                    token_count = health_data["checks"].get("push_tokens", 0)
                    logger.info(f"📱 Backend has {token_count} push tokens registered")
                
                return True
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Backend connection error: {e}")
            return False
    
    def start_bridge(self):
        """Start the connected biometric bridge"""
        logger.info("🚀 Starting Connected Biometric Bridge")
        logger.info("=" * 50)
        logger.info("🎯 This bridge sends REAL push notifications to your phone!")
        logger.info(f"📊 Loaded profiles: {len(self.matcher.profiles)}")
        
        # Test backend connection
        if not self.test_backend_connection():
            logger.error("❌ Cannot connect to backend - notifications will not work")
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return
        
        # MQTT setup
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ Bridge connected to MQTT broker")
                
                # Subscribe to heart rate topics
                topics = [
                    "presient/sensor1/heart_rate/state",
                    "presient/sensor1/sensor/presient_mr60bha2_sensor_heart_rate/state",
                    "presient/sensor1/breath_rate/state",
                    "presient/sensor1/presence/state"
                ]
                
                for topic in topics:
                    client.subscribe(topic)
                    logger.debug(f"📡 Subscribed to: {topic}")
                    
                logger.info("👂 Connected bridge listening - approach sensor to test notifications!")
                
            else:
                logger.error(f"❌ MQTT connection failed: {rc}")
        
        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload = msg.payload.decode('utf-8')
                
                # Heart rate processing
                if "heart_rate" in topic and "/state" in topic:
                    try:
                        heart_rate = float(payload)
                        
                        # Skip fallback values
                        if heart_rate == 40.0:
                            return
                            
                        # Add to matcher
                        sample = BiometricSample(
                            heart_rate=heart_rate,
                            timestamp=datetime.now()
                        )
                        self.matcher.add_sample(sample)
                        
                        logger.debug(f"💓 Processing HR: {heart_rate} BPM")
                        
                        # Check for match and send notification
                        self.check_match_and_notify(heart_rate)
                        
                    except ValueError:
                        pass
                
                # Breathing rate
                elif ("breath_rate" in topic or "breathing_rate" in topic) and "/state" in topic:
                    try:
                        breathing_rate = float(payload)
                        # Add to latest sample
                        if self.matcher.recent_samples:
                            self.matcher.recent_samples[-1].breathing_rate = breathing_rate
                            logger.debug(f"🫁 Added breathing: {breathing_rate} BPM")
                    except ValueError:
                        pass
                        
            except Exception as e:
                logger.error(f"❌ MQTT processing error: {e}")
        
        # Create MQTT client
        client = mqtt.Client(client_id="presient_connected_bridge")
        client.on_connect = on_connect
        client.on_message = on_message
        
        try:
            client.connect(self.mqtt_host, self.mqtt_port, 60)
            client.loop_start()
            
            logger.info("🎯 Connected bridge active! Check your phone for notifications...")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Bridge stopped by user")
                
        except Exception as e:
            logger.error(f"❌ Bridge error: {e}")
        finally:
            client.loop_stop()
            client.disconnect()
    
    def check_match_and_notify(self, heart_rate: float):
        """Check for biometric match and send real notification"""
        try:
            # Check cooldown
            if self.last_match_time:
                time_since = (datetime.now() - self.last_match_time).total_seconds()
                if time_since < self.match_cooldown:
                    return
            
            # Find best match
            match_result = self.matcher.find_best_match(presence_detected=True)
            
            if match_result and match_result.confidence >= 0.75:
                logger.info(f"🎯 BIOMETRIC MATCH: {match_result.name} ({match_result.confidence:.1%})")
                logger.info(f"💓 Heart rate: {heart_rate} BPM matched profile baseline: {match_result.match_details['baseline_heart_rate']:.1f} BPM")
                
                # Send real push notification
                notification_sent = self.send_notification(match_result, heart_rate)
                
                if notification_sent:
                    logger.info("🔔 REAL PUSH NOTIFICATION SENT TO YOUR PHONE!")
                else:
                    logger.warning("⚠️ Notification failed - check backend connection")
                
                # Update tracking
                self.last_match_time = datetime.now()
                self.total_matches += 1
                
                logger.info(f"📊 Total notifications sent: {self.total_matches}")
                
            else:
                current = self.matcher.get_current_biometrics()
                if current:
                    logger.debug(f"🤔 No confident match (HR: {current['heart_rate']:.1f} BPM)")
                    
        except Exception as e:
            logger.error(f"❌ Biometric matching error: {e}")

def main():
    """Main connected bridge function"""
    
    print("📱 Connected Presient Biometric Bridge")
    print("======================================")
    print()
    print("This bridge will:")
    print("✅ Connect to your MR60BHA2 sensor via MQTT")
    print("✅ Perform real-time heart rate matching") 
    print("✅ Send REAL push notifications to your phone")
    print("✅ Use the working /api/presence/event endpoint")
    print()
    
    response = input("Start connected biometric bridge? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ Bridge cancelled")
        return
    
    # Start connected bridge
    bridge = ConnectedBiometricBridge()
    bridge.start_bridge()

if __name__ == "__main__":
    main()