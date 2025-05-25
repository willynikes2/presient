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
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
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
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                
                if self.username and self.password:
                    self.client.username_pw_set(self.username, self.password)
                    
            except Exception as e:
                logger.error(f"Failed to create MQTT client: {e}")
                self.enabled = False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for when client connects"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc, properties=None, flags=None):
        """Callback for when client disconnects"""
        self.connected = False
        logger.info("Disconnected from MQTT broker")
    
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        if not self.enabled or not self.client:
            logger.info("MQTT is disabled or client not initialized")
            return False
        
        try:
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
            logger.error(f"Failed to connect to MQTT broker: {e}")
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
                logger.debug(f"Published to {topic}")
            else:
                logger.error(f"Failed to publish to {topic}, rc={result.rc}")
                
        except Exception as e:
            logger.error(f"Error publishing to MQTT topic {topic}: {e}")
    
    async def publish_presence_event(self, event: PresenceEvent, profile: Optional[Profile] = None):
        """Publish a presence detection event to MQTT"""
        if not self.connected:
            logger.debug("MQTT not connected, skipping presence event publication")
            return
        
        try:
            event_data = {
                "event_id": str(event.id),
                "user_id": event.user_id,
                "sensor_id": event.sensor_id,
                "confidence": event.confidence,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "detected": event.confidence > 0.7
            }
            
            if profile:
                event_data["profile"] = {
                    "name": profile.name,
                    "profile_id": str(profile.id)
                }
            
            await self.publish(
                f"{self.base_topic}/events/presence",
                json.dumps(event_data),
                retain=False
            )
            
            logger.info(f"Published presence event {event.id} to MQTT")
            
        except Exception as e:
            logger.error(f"Error publishing presence event to MQTT: {e}")
    
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
            logger.info("MQTT publisher initialized successfully")
        else:
            logger.warning("MQTT publisher failed to initialize")
    else:
        logger.info("MQTT publisher is disabled")


async def shutdown_mqtt():
    """Cleanup MQTT connection during app shutdown"""
    if mqtt_publisher.connected:
        await mqtt_publisher.disconnect()
        logger.info("MQTT publisher shutdown complete")
