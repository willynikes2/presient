# backend/services/mqtt_publisher.py
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PresenceNotifier:
    def __init__(self, mqtt_broker: str = "192.168.1.102", port: int = 1883, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize MQTT client for Home Assistant integration"""
        self.client = mqtt.Client()
        self.broker = mqtt_broker
        self.port = port
        
        # Set credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        try:
            self.client.connect(mqtt_broker, port, 60)
            self.client.loop_start()  # Start background loop
            logger.info(f"🔗 MQTT client connected to {mqtt_broker}:{port}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ MQTT connected successfully")
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"🔌 MQTT disconnected with code {rc}")
    
    def on_publish(self, client, userdata, mid):
        logger.debug(f"📤 MQTT message {mid} published")

    def publish_detection(self, user_data: Dict[str, Any]):
        """Send detection data to Home Assistant via MQTT"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Main detection payload
            detection_payload = {
                "person": user_data["display_name"],
                "user_id": user_data["user_id"],
                "confidence": user_data["confidence"],
                "location": user_data.get("location", "entrance"),
                "timestamp": timestamp,
                "heart_rate": user_data.get("heart_rate"),
                "breathing_rate": user_data.get("breathing_rate", 16),
                "device_id": "presient_sensor_01",
                "event_type": "person_detected"
            }
            
            # Publish to multiple Home Assistant topics
            topics_and_payloads = [
                # Main detection topic
                ("presient/person_detected", detection_payload),
                
                # Individual user presence
                (f"presient/users/{user_data['user_id']}/presence", "home"),
                
                # Home Assistant device tracker
                ("homeassistant/device_tracker/presient/state", "home"),
                
                # User-specific device tracker  
                (f"homeassistant/device_tracker/presient_{user_data['user_id']}/state", "home"),
                
                # Ring-style notification
                ("presient/notifications/ring_alert", {
                    "title": f"🏠 {user_data['display_name']} is home!",
                    "message": f"Identified with {user_data['confidence']:.1%} confidence",
                    "person": user_data["display_name"],
                    "user_id": user_data["user_id"],
                    "confidence": user_data["confidence"],
                    "timestamp": timestamp,
                    "heart_rate": user_data.get("heart_rate"),
                    "trigger_automations": True  # Flag for Home Assistant automations
                })
            ]
            
            # Publish all messages
            for topic, payload in topics_and_payloads:
                if isinstance(payload, dict):
                    payload_json = json.dumps(payload)
                else:
                    payload_json = str(payload)
                
                result = self.client.publish(topic, payload_json, qos=1, retain=True)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"📤 Published to {topic}: {payload_json[:100]}...")
                else:
                    logger.error(f"❌ Failed to publish to {topic}")
            
            # Special NVIDIA Shield trigger for your user specifically
            # Based on your logs, your user_id is likely "capitalisandme_gmail_com" or "testimg2_gnail_cm"
            shield_users = ["capitalisandme_gmail_com", "testimg2_gnail_cm"]  # Add your user IDs here
            if user_data.get("user_id") in shield_users:
                shield_payload = {
                    "action": "turn_on_shield",
                    "user": user_data["display_name"],
                    "confidence": user_data["confidence"],
                    "timestamp": timestamp
                }
                self.client.publish("presient/nvidia_shield/turn_on", json.dumps(shield_payload), qos=1)
                logger.info(f"🎮 NVIDIA Shield turn-on triggered for {user_data['display_name']}")
                
        except Exception as e:
            logger.error(f"❌ Error publishing MQTT detection: {e}")
    
    def publish_unknown_detection(self, detection_data: Dict[str, Any]):
        """Publish low-confidence/unknown person detection"""
        try:
            unknown_payload = {
                "event_type": "unknown_person",
                "confidence": detection_data["confidence"],
                "heart_rate": detection_data.get("heart_rate"),
                "timestamp": datetime.now().isoformat(),
                "device_id": "presient_sensor_01"
            }
            
            self.client.publish("presient/unknown_detected", json.dumps(unknown_payload), qos=1)
            logger.warning(f"⚠️ Unknown person detected - confidence: {detection_data['confidence']:.1%}")
            
        except Exception as e:
            logger.error(f"❌ Error publishing unknown detection: {e}")
    
    def disconnect(self):
        """Clean disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("🔌 MQTT client disconnected")