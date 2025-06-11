# backend/services/mqtt_subscriber.py
"""
MR60BHA2 mmWave Sensor MQTT Integration for Presient System
Subscribes to real heartbeat data and integrates with existing biometric matching
"""

import paho.mqtt.client as mqtt
import json
import logging
import asyncio
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict
from collections import deque
import statistics
import time

logger = logging.getLogger(__name__)

class MR60BHA2Listener:
    """MQTT listener for MR60BHA2 sensor integration with Presient backend"""
    
    def __init__(self, 
                 broker_host: str = "192.168.1.102",
                 broker_port: int = 1883,
                 sensor_topic_prefix: str = "presient/sensor1"):
        
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.sensor_topic_prefix = sensor_topic_prefix
        
        # MQTT topics
        self.heart_rate_topic = f"{sensor_topic_prefix}/heart_rate/state"
        self.presence_topic = f"{sensor_topic_prefix}/presence/state"
        self.breathing_topic = f"{sensor_topic_prefix}/breathing/state"
        
        # Heart rate data buffer (rolling window)
        self.heart_rate_buffer = deque(maxlen=30)  # ~30 seconds of data
        self.presence_detected = False
        self.last_heartbeat_time = None
        
        # Processing state
        self.processing_lock = threading.Lock()
        self.min_samples_for_auth = 10  # Minimum samples before attempting authentication
        self.stable_reading_threshold = 5.0  # BPM variance threshold for stability
        
        # MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Integration components (set during startup)
        self.biometric_matcher = None
        self.mqtt_publisher = None
        self.notification_system = None
        
        logger.info("🚀 MR60BHA2 MQTT Listener initialized")

    def set_integrations(self, biometric_matcher, mqtt_publisher, notification_system=None):
        """Set integration components from main backend"""
        self.biometric_matcher = biometric_matcher
        self.mqtt_publisher = mqtt_publisher
        self.notification_system = notification_system
        logger.info("✅ Backend integrations configured")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info(f"📡 Connected to MQTT broker {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all sensor topics
            topics = [
                (self.heart_rate_topic, 0),
                (self.presence_topic, 0),
                (self.breathing_topic, 0)
            ]
            
            for topic, qos in topics:
                client.subscribe(topic)
                logger.info(f"📊 Subscribed to: {topic}")
                
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.warning(f"📡 Disconnected from MQTT broker. Return code: {rc}")

    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages from MR60BHA2 sensor"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"📊 MQTT message: {topic} = {payload}")
            
            if topic == self.heart_rate_topic:
                self._process_heart_rate(float(payload))
                
            elif topic == self.presence_topic:
                self._process_presence(payload.lower() == 'true' or payload == '1')
                
            elif topic == self.breathing_topic:
                self._process_breathing_rate(float(payload))
                
        except Exception as e:
            logger.error(f"❌ Error processing MQTT message from {msg.topic}: {e}")

    def _process_heart_rate(self, heart_rate: float):
        """Process real heart rate data from MR60BHA2 sensor"""
        try:
            with self.processing_lock:
                current_time = time.time()
                
                # Validate heart rate reading
                if not (30 <= heart_rate <= 200):
                    logger.warning(f"⚠️ Invalid heart rate reading: {heart_rate} BPM")
                    return
                
                # Add to buffer with timestamp
                self.heart_rate_buffer.append({
                    'bpm': heart_rate,
                    'timestamp': current_time
                })
                
                self.last_heartbeat_time = current_time
                
                logger.info(f"❤️ Heart rate: {heart_rate} BPM (buffer: {len(self.heart_rate_buffer)} samples)")
                
                # Check if we have enough stable data for authentication
                if len(self.heart_rate_buffer) >= self.min_samples_for_auth:
                    self._attempt_biometric_authentication()
                    
        except Exception as e:
            logger.error(f"❌ Error processing heart rate: {e}")

    def _process_presence(self, presence: bool):
        """Process presence detection from MR60BHA2 sensor"""
        try:
            if presence != self.presence_detected:
                self.presence_detected = presence
                
                if presence:
                    logger.info("👤 Presence detected by MR60BHA2 sensor")
                    # Clear buffer to start fresh collection
                    self.heart_rate_buffer.clear()
                else:
                    logger.info("🚪 Presence lost - triggering final authentication attempt")
                    # Try one final authentication with available data
                    if len(self.heart_rate_buffer) >= 5:  # Minimum 5 samples
                        self._attempt_biometric_authentication()
                    self.heart_rate_buffer.clear()
                    
        except Exception as e:
            logger.error(f"❌ Error processing presence: {e}")

    def _process_breathing_rate(self, breathing_rate: float):
        """Process breathing rate for additional validation"""
        logger.debug(f"🫁 Breathing rate: {breathing_rate} breaths/min")
        # Could be used for additional biometric validation in the future

    def _is_heart_rate_stable(self) -> bool:
        """Check if heart rate readings are stable enough for authentication"""
        if len(self.heart_rate_buffer) < 5:
            return False
            
        recent_readings = [sample['bpm'] for sample in list(self.heart_rate_buffer)[-10:]]
        
        if len(recent_readings) < 5:
            return False
            
        std_dev = statistics.stdev(recent_readings)
        return std_dev <= self.stable_reading_threshold

    def _attempt_biometric_authentication(self):
        """Attempt biometric authentication with collected heart rate data"""
        try:
            if not self.biometric_matcher:
                logger.warning("⚠️ Biometric matcher not available")
                return
                
            # Extract heart rate values
            heart_rate_values = [sample['bpm'] for sample in self.heart_rate_buffer]
            
            if len(heart_rate_values) < self.min_samples_for_auth:
                logger.debug(f"📊 Not enough samples for authentication: {len(heart_rate_values)}")
                return
            
            # Check stability
            if not self._is_heart_rate_stable():
                logger.debug("📊 Heart rate not stable enough for authentication")
                return
                
            logger.info(f"🔍 Attempting biometric authentication with {len(heart_rate_values)} heart rate samples")
            logger.info(f"📊 HR Stats: avg={statistics.mean(heart_rate_values):.1f}, "
                       f"std={statistics.stdev(heart_rate_values):.1f}, "
                       f"range={max(heart_rate_values)-min(heart_rate_values):.1f}")
            
            # Use existing biometric matcher
            match_result = self.biometric_matcher.match_profile(heart_rate_values)
            
            if match_result:
                person = match_result["user_id"]
                confidence = match_result["confidence"]
                
                logger.info(f"✅ Person identified: {person} with {confidence:.1%} confidence")
                
                # Trigger presence event through existing system
                asyncio.create_task(self._trigger_presence_event(person, confidence, heart_rate_values))
                
                # Clear buffer after successful authentication
                self.heart_rate_buffer.clear()
                
            else:
                logger.info("❌ No biometric match found with current heart rate data")
                
        except Exception as e:
            logger.error(f"❌ Error during biometric authentication: {e}")

    async def _trigger_presence_event(self, person: str, confidence: float, heart_rate_data: List[float]):
        """Trigger presence event through existing Presient backend system"""
        try:
            # Prepare event data in the format expected by existing backend
            event_data = {
                "person": person,
                "confidence": confidence,
                "sensor_id": "mr60bha2_sensor_1",
                "location": "MR60BHA2 Detection Zone", 
                "source": "mr60bha2_mmwave",
                "heart_rate": heart_rate_data,
                "mean_hr": statistics.mean(heart_rate_data),
                "std_hr": statistics.stdev(heart_rate_data) if len(heart_rate_data) > 1 else 0,
                "range_hr": max(heart_rate_data) - min(heart_rate_data),
                "sample_count": len(heart_rate_data),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"🚀 Triggering presence event for {person} via MR60BHA2")
            
            # Option 1: Use existing Ring-style notification system (if available)
            if self.notification_system:
                await self.notification_system.trigger_presence_notification(
                    person=person,
                    confidence=confidence,
                    sensor_id="mr60bha2_sensor_1",
                    location="MR60BHA2 Detection Zone",
                    source="mr60bha2_mmwave"
                )
            
            # Option 2: Publish enhanced MQTT message with detection details
            if self.mqtt_publisher and self.mqtt_publisher.connected:
                mqtt_payload = {
                    "person": person,
                    "confidence": confidence,
                    "source": "mr60bha2_mmwave",
                    "sensor_id": "mr60bha2_sensor_1",
                    "location": "MR60BHA2 Detection Zone",
                    "timestamp": event_data["timestamp"],
                    "trigger_action": "presence_detected",
                    "sensor_data": {
                        "mean_hr": event_data["mean_hr"],
                        "sample_count": event_data["sample_count"],
                        "detection_quality": "high" if confidence > 0.9 else "medium"
                    }
                }
                
                topic = f"{self.mqtt_publisher.base_topic}/presence/mr60bha2_detected"
                await self.mqtt_publisher.publish(topic, json.dumps(mqtt_payload), retain=False)
                logger.info(f"📡 Published MR60BHA2 detection to MQTT: {topic}")
            
            # Option 3: Could also call existing FastAPI endpoint directly
            # This would integrate with the Ring-style notification system
            
        except Exception as e:
            logger.error(f"❌ Error triggering presence event: {e}")

    def start_listening(self):
        """Start the MQTT listener"""
        try:
            logger.info(f"🚀 Starting MR60BHA2 MQTT listener...")
            logger.info(f"📡 Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the MQTT loop in a separate thread
            self.client.loop_start()
            
            logger.info("✅ MR60BHA2 MQTT listener started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start MQTT listener: {e}")
            raise

    def stop_listening(self):
        """Stop the MQTT listener"""
        try:
            logger.info("🛑 Stopping MR60BHA2 MQTT listener...")
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("✅ MR60BHA2 MQTT listener stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping MQTT listener: {e}")

    def get_status(self) -> Dict:
        """Get current status of the MR60BHA2 listener"""
        return {
            "connected": self.client.is_connected(),
            "broker": f"{self.broker_host}:{self.broker_port}",
            "topics": {
                "heart_rate": self.heart_rate_topic,
                "presence": self.presence_topic,
                "breathing": self.breathing_topic
            },
            "buffer_size": len(self.heart_rate_buffer),
            "presence_detected": self.presence_detected,
            "last_heartbeat": self.last_heartbeat_time,
            "biometric_matcher_ready": self.biometric_matcher is not None,
            "mqtt_publisher_ready": self.mqtt_publisher is not None
        }


# Integration function for main backend
async def initialize_mr60bha2_listener(biometric_matcher, mqtt_publisher, notification_system=None):
    """Initialize MR60BHA2 listener and integrate with backend components"""
    try:
        # Create listener instance
        mr60bha2_listener = MR60BHA2Listener()
        
        # Set integration components
        mr60bha2_listener.set_integrations(
            biometric_matcher=biometric_matcher,
            mqtt_publisher=mqtt_publisher,
            notification_system=notification_system
        )
        
        # Start listening
        mr60bha2_listener.start_listening()
        
        logger.info("🎉 MR60BHA2 sensor integration initialized successfully")
        return mr60bha2_listener
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MR60BHA2 integration: {e}")
        raise


# Global instance for backend integration
mr60bha2_listener: Optional[MR60BHA2Listener] = None


async def startup_mr60bha2_integration(biometric_matcher, mqtt_publisher, notification_system=None):
    """Startup function for MR60BHA2 integration"""
    global mr60bha2_listener
    
    try:
        mr60bha2_listener = await initialize_mr60bha2_listener(
            biometric_matcher=biometric_matcher,
            mqtt_publisher=mqtt_publisher,
            notification_system=notification_system
        )
        logger.info("✅ MR60BHA2 integration started")
        
    except Exception as e:
        logger.error(f"❌ Failed to start MR60BHA2 integration: {e}")


async def shutdown_mr60bha2_integration():
    """Shutdown function for MR60BHA2 integration"""
    global mr60bha2_listener
    
    if mr60bha2_listener:
        try:
            mr60bha2_listener.stop_listening()
            mr60bha2_listener = None
            logger.info("✅ MR60BHA2 integration stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping MR60BHA2 integration: {e}")


def get_mr60bha2_status():
    """Get current status of MR60BHA2 integration"""
    global mr60bha2_listener
    
    if mr60bha2_listener:
        return mr60bha2_listener.get_status()
    else:
        return {"error": "MR60BHA2 listener not initialized"}