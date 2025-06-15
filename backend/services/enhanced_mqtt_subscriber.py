#!/usr/bin/env python3
"""
Enhanced MQTT Subscriber with Real Biometric Matching
Processes MR60BHA2 sensor data with real authentication
"""

import asyncio
import json
import logging
import httpx
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading
import statistics

# Import our real biometric matcher
from .real_biometric_matcher import RealBiometricMatcher, BiometricProfile, BiometricSample

logger = logging.getLogger(__name__)

class EnhancedMQTTSubscriber:
    """Enhanced MQTT subscriber with real biometric matching"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        
        # Real biometric matcher
        self.matcher = RealBiometricMatcher()
        
        # MQTT client
        self.mqtt_client = mqtt.Client(client_id="presient_enhanced_subscriber")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        
        # Detection state
        self.last_detection_time = None
        self.detection_cooldown = 30  # seconds
        self.auth_token = None
        
        # Load profiles on startup
        asyncio.create_task(self._load_profiles())
    
    def _on_connect(self, client, userdata, flags, rc):
        """Subscribe to sensor topics"""
        if rc == 0:
            logger.info("✅ Enhanced MQTT subscriber connected")
            
            topics = [
                "presient/sensor1/heart_rate/state",
                "presient/sensor1/breath_rate/state",
                "presient/sensor1/sensor/presient_mr60bha2_sensor_heart_rate/state",
                "presient/sensor1/sensor/presient_mr60bha2_sensor_breathing_rate/state",
                "presient/sensor1/status"
            ]
            
            for topic in topics:
                client.subscribe(topic)
            
            logger.info("👂 Enhanced biometric matching active")
        else:
            logger.error(f"❌ MQTT connection failed: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Process sensor data with real matching"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Heart rate processing
            if "heart_rate" in topic and "/state" in topic:
                try:
                    heart_rate = float(payload)
                    
                    # Add to matcher
                    sample = BiometricSample(
                        heart_rate=heart_rate,
                        timestamp=datetime.now()
                    )
                    self.matcher.add_sample(sample)
                    
                    logger.info(f"💓 Heart rate: {heart_rate} BPM")
                    
                    # Process detection
                    threading.Thread(target=self._process_detection_sync).start()
                    
                except ValueError:
                    pass
            
            # Breathing rate
            elif ("breath_rate" in topic or "breathing_rate" in topic) and "/state" in topic:
                try:
                    breathing_rate = float(payload)
                    # Update latest sample with breathing rate
                    if self.matcher.recent_samples:
                        self.matcher.recent_samples[-1].breathing_rate = breathing_rate
                    logger.debug(f"🫁 Breathing: {breathing_rate} BPM")
                except ValueError:
                    pass
            
            # Presence status
            elif "status" in topic:
                presence = payload.upper() in ["ON", "TRUE", "1"]
                if presence:
                    logger.info("👤 Presence detected by sensor")
                    
        except Exception as e:
            logger.error(f"❌ MQTT processing error: {e}")
    
    def _process_detection_sync(self):
        """Sync wrapper for detection processing"""
        try:
            asyncio.run(self._process_detection())
        except Exception as e:
            logger.error(f"❌ Detection error: {e}")
    
    async def _process_detection(self):
        """Enhanced detection with real biometric matching"""
        try:
            # Check cooldown
            if self.last_detection_time:
                time_since = (datetime.now() - self.last_detection_time).total_seconds()
                if time_since < self.detection_cooldown:
                    return
            
            # Find best match using real algorithm
            match_result = self.matcher.find_best_match(presence_detected=True)
            
            if match_result and match_result.confidence >= 0.80:
                logger.info(f"🎯 REAL MATCH: {match_result.name} ({match_result.confidence:.1%})")
                
                # Send to backend
                success = await self._send_detection_to_backend(match_result)
                
                if success:
                    self.last_detection_time = datetime.now()
                    logger.info("🎉 Real biometric detection complete!")
                    
            else:
                current = self.matcher.get_current_biometrics()
                if current:
                    logger.info(f"🤔 No confident match (HR: {current['heart_rate']:.1f} BPM)")
                    
        except Exception as e:
            logger.error(f"❌ Detection processing error: {e}")
    
    async def _send_detection_to_backend(self, match_result) -> bool:
        """Send real detection result to backend"""
        try:
            if not self.auth_token:
                await self._authenticate()
            
            current = self.matcher.get_current_biometrics()
            
            event_data = {
                "sensor_id": "presient-sensor-1",
                "heart_rate": current["heart_rate"] if current else 0,
                "breathing_rate": current.get("breathing_rate"),
                "confidence": match_result.confidence,
                "source": "real_biometric_matching",
                "matched_user_id": match_result.user_id,
                "match_details": match_result.match_details,
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/presence/event",
                    json=event_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 201:
                    logger.info("✅ Real detection sent to backend")
                    return True
                else:
                    logger.error(f"❌ Backend error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Backend communication error: {e}")
            return False
    
    async def _load_profiles(self):
        """Load user profiles from backend"""
        try:
            # Authenticate first
            await self._authenticate()
            
            if not self.auth_token:
                logger.error("❌ Could not authenticate to load profiles")
                return
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/profiles",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    profiles_data = response.json()
                    
                    for profile_data in profiles_data:
                        profile = BiometricProfile(
                            user_id=profile_data.get("user_id", profile_data["id"]),
                            name=profile_data.get("name", "Unknown"),
                            heart_rate_baseline=profile_data.get("heart_rate_baseline", 75.0),
                            heart_rate_range=profile_data.get("heart_rate_range", [60, 100]),
                            heart_rate_stdev=profile_data.get("heart_rate_stdev", 5.0),
                            breathing_rate_baseline=profile_data.get("breathing_rate_baseline"),
                            confidence_threshold=profile_data.get("biometric_confidence_threshold", 0.80)
                        )
                        
                        self.matcher.add_profile(profile)
                    
                    logger.info(f"✅ Loaded {len(profiles_data)} biometric profiles")
                else:
                    logger.error(f"❌ Failed to load profiles: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Profile loading error: {e}")
    
    async def _authenticate(self):
        """Authenticate with backend"""
        try:
            auth_data = {
                "username": "sensor_integration",
                "password": "sensor_password_123"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/auth/login",
                    data=auth_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.auth_token = result["access_token"]
                    logger.info("✅ Enhanced subscriber authenticated")
                else:
                    logger.error(f"❌ Authentication failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
    
    def start(self):
        """Start enhanced MQTT subscriber"""
        logger.info("🚀 Starting enhanced MQTT subscriber with real biometric matching")
        
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.mqtt_client.loop_start()
        
        logger.info("✅ Enhanced real biometric matching active!")

# Global instance
enhanced_subscriber = None

def initialize_enhanced_subscriber():
    """Initialize the enhanced subscriber"""
    global enhanced_subscriber
    enhanced_subscriber = EnhancedMQTTSubscriber()
    enhanced_subscriber.start()
    return enhanced_subscriber
