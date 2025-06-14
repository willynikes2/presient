# Fixed MQTT service using paho-mqtt (which is already installed)
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
import asyncio

import paho.mqtt.client as mqtt

from backend.models.presence_events import PresenceEvent
from backend.models.profile import Profile

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """MQTT Publisher service using paho-mqtt"""
    
    def __init__(self):
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "192.168.1.102")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        # ✅ Fixed: Added default values for username/password
        self.username = os.getenv("MQTT_USERNAME", "presient")
        self.password = os.getenv("MQTT_PASSWORD", "presient123")
        self.client_id = os.getenv("MQTT_CLIENT_ID", "presient-api")
        
        # Topic configuration
        self.base_topic = os.getenv("MQTT_BASE_TOPIC", "presient")
        self.discovery_prefix = os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant")
        
        # Connection management
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.enabled = os.getenv("MQTT_ENABLED", "true").lower() == "true"
        
        # Initialize client if enabled
        if self.enabled:
            try:
                # ✅ Fixed: Correct syntax for paho-mqtt 2.1.0
                self.client = mqtt.Client(
                    client_id=self.client_id
                )
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                
                if self.username and self.password:
                    self.client.username_pw_set(self.username, self.password)
                    logger.info(f"🔐 MQTT credentials configured for user: {self.username}")
                    
            except Exception as e:
                logger.error(f"Failed to create MQTT client: {e}")
                self.enabled = False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for when client connects"""
        if rc == 0:
            self.connected = True
            logger.info(f"🔗 Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier", 
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            error_msg = error_messages.get(rc, f"Unknown error code {rc}")
            logger.error(f"❌ Failed to connect to MQTT broker, return code {rc}: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc, properties=None, flags=None):
        """Callback for when client disconnects"""
        self.connected = False
        logger.info("🔌 Disconnected from MQTT broker")
    
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        if not self.enabled or not self.client:
            logger.info("MQTT is disabled or client not initialized")
            return False
        
        try:
            logger.info(f"🔄 Attempting MQTT connection to {self.broker_host}:{self.broker_port}")
            # Connect in a non-blocking way
            self.client.connect_async(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait a bit for connection
            for _ in range(10):  # Wait up to 5 seconds
                if self.connected:
                    await self.publish_status("online")
                    return True
                await asyncio.sleep(0.5)
            
            logger.warning("MQTT connection timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.connected:
            try:
                await self.publish_status("offline")
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
            finally:
                self.connected = False
    
    async def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish a message to MQTT topic"""
        if not self.connected or not self.client:
            logger.debug(f"MQTT not connected, skipping publish to {topic}")
            return
        
        try:
            result = self.client.publish(topic, payload, retain=retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"📤 Published to {topic}")
            else:
                logger.error(f"❌ Failed to publish to {topic}, rc={result.rc}")
                
        except Exception as e:
            logger.error(f"❌ Error publishing to MQTT topic {topic}: {e}")
    
    async def publish_presence_event(self, event: PresenceEvent, profile: Optional[Profile] = None):
        """Publish a presence detection event to MQTT for Home Assistant"""
        if not self.connected:
            logger.debug("MQTT not connected, skipping presence event publication")
            return
        
        try:
            # Home Assistant compatible format
            event_data = {
                "person": event.user_id,  # Display name
                "user_id": event.user_id,
                "confidence": event.confidence,
                "location": "entrance",  # Default location
                "timestamp": event.timestamp.isoformat() if event.timestamp is not None else datetime.now().isoformat(),
                "heart_rate": getattr(event, 'heart_rate', None),
                "breathing_rate": getattr(event, 'breathing_rate', 16),
                "device_id": "presient_sensor_01",
                "event_type": "person_detected"
            }
            
            # Add profile info if available
            if profile:
                event_data["person"] = profile.name  # Use actual name instead of user_id
                event_data["profile_id"] = str(profile.id)
            
            # Publish to Home Assistant topic (what the automation expects)
            await self.publish(
                "presient/person_detected",  # Home Assistant automation topic
                json.dumps(event_data),
                retain=True  # Retain for Home Assistant
            )
            
            # Also publish to original topic for compatibility
            await self.publish(
                f"{self.base_topic}/events/presence",
                json.dumps({
                    "event_id": str(event.id),
                    "user_id": event.user_id,
                    "sensor_id": event.sensor_id,
                    "confidence": event.confidence,
                    "timestamp": event.timestamp.isoformat() if event.timestamp is not None else None,
                    "detected": event.confidence > 0.7
                }),
                retain=False
            )
            
            # NVIDIA Shield specific trigger for certain users
            shield_users = ["capitalisandme_gmail_com", "testimg2_gnail_cm", "jane_smith"]
            shield_trigger = False
            if event.user_id in shield_users and event.confidence is not None:
                # If event.confidence is a SQLAlchemy ColumnElement, use .is_(True)
                if hasattr(event.confidence, "is_"):
                    shield_trigger = event.confidence.is_(True)
                else:
                    shield_trigger = event.confidence > 0.80

            # Avoid using SQLAlchemy expressions directly in if statements
            should_trigger = bool(shield_trigger)
            if should_trigger:
                shield_data = {
                    "action": "turn_on_shield",
                    "user": event.user_id,
                    "confidence": float(event.confidence) if hasattr(event.confidence, "__float__") else event.confidence,
                    "timestamp": datetime.now().isoformat()
                }
                await self.publish(
                    "presient/nvidia_shield/turn_on",
                    json.dumps(shield_data),
                    retain=False
                )
                logger.info(f"🎮 NVIDIA Shield trigger published for {event.user_id}")
            
            logger.info(f"📤 Published presence event {event.id} to MQTT (HA compatible)")
            
        except Exception as e:
            logger.error(f"❌ Error publishing presence event to MQTT: {e}")
    
    async def publish_status(self, status: str):
        """Publish system status"""
        try:
            await self.publish(
                f"{self.base_topic}/status",
                status,
                retain=True
            )
        except Exception as e:
            logger.error(f"Error publishing status to MQTT: {e}")
    
    async def publish_sensor_registration(self, sensor_id: str, sensor_data: Dict[str, Any]):
        """Publish sensor registration"""
        if not self.connected:
            return
        
        try:
            registration_data = {
                "sensor_id": sensor_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "registered",
                **sensor_data
            }
            
            await self.publish(
                f"{self.base_topic}/sensors/{sensor_id}/registration",
                json.dumps(registration_data),
                retain=True
            )
            
        except Exception as e:
            logger.error(f"Error publishing sensor registration: {e}")
    
    async def publish_heartbeat(self, sensor_id: str):
        """Publish sensor heartbeat"""
        if not self.connected:
            return
        
        try:
            heartbeat_data = {
                "sensor_id": sensor_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "alive"
            }
            
            await self.publish(
                f"{self.base_topic}/sensors/{sensor_id}/heartbeat",
                json.dumps(heartbeat_data),
                retain=False
            )
            
        except Exception as e:
            logger.error(f"Error publishing heartbeat: {e}")
    
    async def publish_user_status(self, user_id: str, status: str):
        """Publish user online/offline status"""
        if not self.connected:
            return
            
        try:
            status_data = {
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.publish(
                f"{self.base_topic}/users/{user_id}/status",
                json.dumps(status_data),
                retain=True
            )
            
        except Exception as e:
            logger.error(f"Error publishing user status: {e}")
    
    async def publish_light_command(self, color: str, user_id: Optional[str] = None, duration: int = 3) -> bool:
        """Publish light control command to ESP32"""
        if not self.connected:
            logger.debug("MQTT not connected, skipping light command")
            return False
        
        try:
            # Color command mapping
            color_commands = {
                "off": {"state": "OFF"},
                "blue": {"state": "ON", "color": {"r": 0, "g": 50, "b": 255}},
                "green": {"state": "ON", "color": {"r": 0, "g": 255, "b": 0}},
                "yellow": {"state": "ON", "color": {"r": 255, "g": 255, "b": 0}},
                "purple": {"state": "ON", "color": {"r": 128, "g": 0, "b": 255}},
                "red": {"state": "ON", "color": {"r": 255, "g": 0, "b": 0}}
            }
            
            command = color_commands.get(color, color_commands["blue"])
            
            # Enhanced command with metadata
            enhanced_command = {
                **command,
                "user_id": user_id,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "presient_auth"
            }
            
            # Publish to ESP32 light topic
            topic = f"{self.base_topic}/princeton/light/status_light/command"
            
            await self.publish(
                topic,
                json.dumps(enhanced_command),
                retain=False
            )
            
            logger.info(f"Published {color} light command for user {user_id} to {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing light command: {e}")
            return False

    def get_mqtt_status(self) -> Dict[str, Any]:
        """Get comprehensive MQTT status"""
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "broker_host": self.broker_host,
            "broker_port": self.broker_port,
            "client_id": self.client_id,
            "base_topic": self.base_topic,
            "has_auth": bool(self.username and self.password)
        }
    
    def get_uptime(self) -> Optional[float]:
        """Get connection uptime in seconds"""
        # This is a placeholder - would need to track connection time
        return None


# Global MQTT publisher instance
mqtt_publisher = MQTTPublisher()


async def initialize_mqtt():
    """Initialize MQTT connection during app startup"""
    if mqtt_publisher.enabled:
        success = await mqtt_publisher.connect()
        if success:
            logger.info("✅ MQTT publisher initialized successfully")
        else:
            logger.warning("⚠️ MQTT publisher failed to initialize")
    else:
        logger.info("ℹ️ MQTT publisher is disabled")


async def shutdown_mqtt():
    """Cleanup MQTT connection during app shutdown"""
    if mqtt_publisher.connected:
        await mqtt_publisher.disconnect()
        logger.info("🔌 MQTT publisher shutdown complete")