# backend/services/mqtt.py
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import os

try:
    import aiomqtt
except ImportError:
    aiomqtt = None

from backend.models.presence_events import PresenceEvent
from backend.models.profile import Profile

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """
    MQTT Publisher service for publishing presence detection results.
    Supports Home Assistant MQTT Discovery and custom topic structures.
    """
    
    def __init__(self):
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self.client_id = os.getenv("MQTT_CLIENT_ID", "presient-api")
        
        # Topic configuration
        self.base_topic = os.getenv("MQTT_BASE_TOPIC", "presient")
        self.discovery_prefix = os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant")
        
        # Connection management
        self.client: Optional[aiomqtt.Client] = None
        self.connected = False
        
        # Check if MQTT is available
        if aiomqtt is None:
            logger.warning("aiomqtt not installed. MQTT functionality disabled.")
            self.enabled = False
        else:
            self.enabled = os.getenv("MQTT_ENABLED", "true").lower() == "true"
    
    async def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if not self.enabled or aiomqtt is None:
            logger.info("MQTT is disabled or aiomqtt not available")
            return False
        
        try:
            self.client = aiomqtt.Client(
                hostname=self.broker_host,
                port=self.broker_port,
                username=self.username,
                password=self.password,
                identifier=self.client_id
            )
            
            await self.client.connect()
            self.connected = True
            
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Publish online status
            await self.publish_status("online")
            
            # Setup Home Assistant discovery if enabled
            if os.getenv("MQTT_HOMEASSISTANT_DISCOVERY", "true").lower() == "true":
                await self.setup_homeassistant_discovery()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client and self.connected:
            try:
                # Publish offline status before disconnecting
                await self.publish_status("offline")
                await self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
            finally:
                self.connected = False
                self.client = None
    
    async def publish_presence_event(self, event: PresenceEvent, profile: Optional[Profile] = None):
        """
        Publish a presence detection event to MQTT.
        
        Args:
            event: The presence event to publish
            profile: Optional profile information for the detected user
        """
        if not self.connected or not self.client:
            logger.debug("MQTT not connected, skipping presence event publication")
            return
        
        try:
            # Prepare event data
            event_data = {
                "event_id": event.id,
                "user_id": event.user_id,
                "sensor_id": event.sensor_id,
                "confidence": event.confidence,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "detected": event.confidence > 0.7,  # Threshold for "presence detected"
            }
            
            # Add profile information if available
            if profile:
                event_data["profile"] = {
                    "name": profile.name,
                    "profile_id": profile.id
                }
            
            # Publish to multiple topic structures for different integrations
            await self._publish_event_topics(event_data)
            
            logger.info(f"Published presence event {event.id} to MQTT")
            
        except Exception as e:
            logger.error(f"Error publishing presence event to MQTT: {e}")
    
    async def _publish_event_topics(self, event_data: Dict[str, Any]):
        """Publish event to multiple topic structures."""
        
        # Determine user display name
        if "profile" in event_data and event_data["profile"]:
            user_name = event_data["profile"]["name"]
            user_status = f"detected_{user_name.lower().replace(' ', '_')}"
        else:
            user_name = "Unregistered Person"
            user_status = "detected_unregistered"
        
        # 1. Raw event topic (JSON payload)
        await self.publish(
            f"{self.base_topic}/events/presence",
            json.dumps(event_data),
            retain=False
        )
        
        # 2. User-specific topic
        await self.publish(
            f"{self.base_topic}/users/{event_data['user_id']}/presence",
            "detected" if event_data["detected"] else "not_detected",
            retain=True
        )
        
        # 3. Sensor-specific topic
        await self.publish(
            f"{self.base_topic}/sensors/{event_data['sensor_id']}/last_event",
            json.dumps(event_data),
            retain=True
        )
        
        # 4. Home Assistant compatible topics - Main presence detection
        await self.publish(
            f"{self.base_topic}/binary_sensor/presence_detected/state",
            "ON" if event_data["detected"] else "OFF",
            retain=True
        )
        
        # 5. Detected person name topic (for display in HA)
        detected_person = user_name if event_data["detected"] else "Nobody"
        await self.publish(
            f"{self.base_topic}/sensor/detected_person/state",
            detected_person,
            retain=True
        )
        
        # 6. Last detection details (JSON with full info)
        detection_details = {
            "person": user_name,
            "confidence": event_data["confidence"],
            "timestamp": event_data["timestamp"],
            "sensor": event_data["sensor_id"],
            "registered": "profile" in event_data and event_data["profile"] is not None
        }
        await self.publish(
            f"{self.base_topic}/sensor/last_detection/state",
            json.dumps(detection_details),
            retain=True
        )
        
        # 7. Confidence level topic
        await self.publish(
            f"{self.base_topic}/sensor/confidence/state",
            str(round(event_data["confidence"] * 100, 1)),
            retain=True
        )
        
        # 8. Detection status with person name
        await self.publish(
            f"{self.base_topic}/sensor/detection_status/state",
            user_status if event_data["detected"] else "no_detection",
            retain=True
        )
    
    async def publish_status(self, status: str):
        """Publish system status (online/offline)."""
        if not self.connected or not self.client:
            return
        
        try:
            await self.publish(
                f"{self.base_topic}/status",
                status,
                retain=True
            )
            
            # Also publish with timestamp
            status_data = {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            
            await self.publish(
                f"{self.base_topic}/system/status",
                json.dumps(status_data),
                retain=True
            )
            
        except Exception as e:
            logger.error(f"Error publishing status to MQTT: {e}")
    
    async def setup_homeassistant_discovery(self):
        """Setup Home Assistant MQTT Discovery configuration."""
        try:
            # Binary sensor for presence detection
            presence_config = {
                "name": "Presient Presence Detected",
                "unique_id": "presient_presence_detected",
                "state_topic": f"{self.base_topic}/binary_sensor/presence_detected/state",
                "device_class": "presence",
                "payload_on": "ON",
                "payload_off": "OFF",
                "icon": "mdi:account-check",
                "device": {
                    "identifiers": ["presient_api"],
                    "name": "Presient Biometric System",
                    "model": "mmWave Heartbeat Detection",
                    "manufacturer": "Presient",
                    "sw_version": "1.0.0"
                }
            }
            
            await self.publish(
                f"{self.discovery_prefix}/binary_sensor/presient/presence_detected/config",
                json.dumps(presence_config),
                retain=True
            )
            
            # Sensor for detected person name
            person_config = {
                "name": "Presient Detected Person",
                "unique_id": "presient_detected_person",
                "state_topic": f"{self.base_topic}/sensor/detected_person/state",
                "icon": "mdi:account",
                "device": {
                    "identifiers": ["presient_api"],
                    "name": "Presient Biometric System",
                    "model": "mmWave Heartbeat Detection",
                    "manufacturer": "Presient",
                    "sw_version": "1.0.0"
                }
            }
            
            await self.publish(
                f"{self.discovery_prefix}/sensor/presient/detected_person/config",
                json.dumps(person_config),
                retain=True
            )
            
            # Sensor for confidence level
            confidence_config = {
                "name": "Presient Detection Confidence",
                "unique_id": "presient_confidence",
                "state_topic": f"{self.base_topic}/sensor/confidence/state",
                "unit_of_measurement": "%",
                "icon": "mdi:percent",
                "device": {
                    "identifiers": ["presient_api"],
                    "name": "Presient Biometric System",
                    "model": "mmWave Heartbeat Detection",
                    "manufacturer": "Presient",
                    "sw_version": "1.0.0"
                }
            }
            
            await self.publish(
                f"{self.discovery_prefix}/sensor/presient/confidence/config",
                json.dumps(confidence_config),
                retain=True
            )
            
            # Sensor for last detection details (JSON attributes)
            detection_details_config = {
                "name": "Presient Last Detection",
                "unique_id": "presient_last_detection",
                "state_topic": f"{self.base_topic}/sensor/last_detection/state",
                "icon": "mdi:radar",
                "value_template": "{{ value_json.person }}",
                "json_attributes_topic": f"{self.base_topic}/sensor/last_detection/state",
                "device": {
                    "identifiers": ["presient_api"],
                    "name": "Presient Biometric System",
                    "model": "mmWave Heartbeat Detection",
                    "manufacturer": "Presient",
                    "sw_version": "1.0.0"
                }
            }
            
            await self.publish(
                f"{self.discovery_prefix}/sensor/presient/last_detection/config",
                json.dumps(detection_details_config),
                retain=True
            )
            
            # Sensor for detection status (includes person identification)
            status_config = {
                "name": "Presient Detection Status",
                "unique_id": "presient_detection_status",
                "state_topic": f"{self.base_topic}/sensor/detection_status/state",
                "icon": "mdi:motion-sensor",
                "device": {
                    "identifiers": ["presient_api"],
                    "name": "Presient Biometric System",
                    "model": "mmWave Heartbeat Detection",
                    "manufacturer": "Presient",
                    "sw_version": "1.0.0"
                }
            }
            
            await self.publish(
                f"{self.discovery_prefix}/sensor/presient/detection_status/config",
                json.dumps(status_config),
                retain=True
            )
            
            logger.info("Home Assistant MQTT Discovery configuration published")
            
        except Exception as e:
            logger.error(f"Error setting up Home Assistant discovery: {e}")
    
    async def publish(self, topic: str, payload: str, retain: bool = False):
        """
        Publish a message to MQTT topic.
        
        Args:
            topic: MQTT topic
            payload: Message payload
            retain: Whether to retain the message
        """
        if not self.connected or not self.client:
            logger.debug(f"MQTT not connected, skipping publish to {topic}")
            return
        
        try:
            await self.client.publish(topic, payload, retain=retain)
            logger.debug(f"Published to {topic}: {payload}")
            
        except Exception as e:
            logger.error(f"Error publishing to MQTT topic {topic}: {e}")
    
    async def publish_sensor_registration(self, sensor_id: str, sensor_data: Dict[str, Any]):
        """
        Publish sensor registration/discovery information.
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_data: Sensor metadata (location, capabilities, etc.)
        """
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
            
            logger.info(f"Published sensor registration for {sensor_id}")
            
        except Exception as e:
            logger.error(f"Error publishing sensor registration: {e}")
    
    async def publish_heartbeat(self, sensor_id: str):
        """Publish sensor heartbeat/keepalive."""
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
            logger.error(f"Error publishing heartbeat for {sensor_id}: {e}")


# Global MQTT publisher instance
mqtt_publisher = MQTTPublisher()


async def initialize_mqtt():
    """Initialize MQTT connection during app startup."""
    if mqtt_publisher.enabled:
        success = await mqtt_publisher.connect()
        if success:
            logger.info("MQTT publisher initialized successfully")
        else:
            logger.warning("MQTT publisher failed to initialize")
    else:
        logger.info("MQTT publisher is disabled")


async def shutdown_mqtt():
    """Cleanup MQTT connection during app shutdown."""
    if mqtt_publisher.connected:
        await mqtt_publisher.disconnect()
        logger.info("MQTT publisher shutdown complete")