
"""
MR60BHA2 MQTT Subscriber Service for Presient Backend
Connects to Home Assistant MQTT and processes real heart rate data.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("backend.services.mqtt_subscriber")

# Global variables for service state
mqtt_client = None
mr60bha2_status = {
    "connected": False,
    "last_heartbeat": None,
    "last_error": None,
    "heart_rate_buffer": [],
    "presence_detected": False
}

# Accept incoming references from the backend (optional in MVP)
biometric_matcher = None
automation_settings = {}

def get_mr60bha2_status() -> Dict[str, Any]:
    return {
        "connected": mr60bha2_status["connected"],
        "last_heartbeat": mr60bha2_status["last_heartbeat"],
        "buffer_size": len(mr60bha2_status["heart_rate_buffer"]),
        "presence_detected": mr60bha2_status["presence_detected"],
        "topics": [
            "homeassistant/sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_heart_rate/state",
            "homeassistant/sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_breathing_rate/state",
            "homeassistant/binary_sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_presence/state"
        ],
        "last_error": mr60bha2_status["last_error"]
    }

async def startup_mr60bha2_integration(biometric=None, automation=None):
    global mqtt_client, biometric_matcher, automation_settings

    if biometric:
        biometric_matcher = biometric
    if automation:
        automation_settings = automation

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("âš ï¸ paho-mqtt not installed.")
        mr60bha2_status["last_error"] = "paho-mqtt not installed"
        return False

    mqtt_client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("âœ… Connected to MQTT broker")
            mr60bha2_status["connected"] = True
            for topic in get_mr60bha2_status()["topics"]:
                client.subscribe(topic)
                logger.debug(f"ðŸ“¡ Subscribed to: {topic}")
        else:
            logger.error(f"âŒ MQTT connection failed: {rc}")
            mr60bha2_status["last_error"] = f"Connection failed: {rc}"

    def on_message(client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        logger.debug(f"MQTT Message: {topic} = {payload}")
        try:
            if "heart_rate/state" in topic:
                heart_rate = float(payload)
                if 40 <= heart_rate <= 180:
                    mr60bha2_status["heart_rate_buffer"].append({
                        "value": heart_rate,
                        "timestamp": datetime.now().isoformat()
                    })
                    if len(mr60bha2_status["heart_rate_buffer"]) > 30:
                        mr60bha2_status["heart_rate_buffer"].pop(0)
                    mr60bha2_status["last_heartbeat"] = datetime.now().isoformat()
                    logger.info(f"ðŸ’“ Heart rate: {heart_rate} BPM")
            elif "presence/state" in topic:
                mr60bha2_status["presence_detected"] = payload.lower() in ["on", "true", "1"]
                logger.info(f"ðŸ‘¤ Presence: {'detected' if mr60bha2_status['presence_detected'] else 'cleared'}")
        except Exception as e:
            logger.error(f"âŒ Error in on_message: {e}")
            mr60bha2_status["last_error"] = str(e)

    def on_disconnect(client, userdata, rc):
        logger.warning(f"âš ï¸ MQTT disconnected: {rc}")
        mr60bha2_status["connected"] = False

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    try:
        mqtt_client.connect("192.168.1.102", 1883, 60)
        mqtt_client.loop_start()
        logger.info("ðŸš€ MR60BHA2 MQTT integration running")
        return True
    except Exception as e:
        logger.error(f"âŒ MQTT connection exception: {e}")
        mr60bha2_status["last_error"] = str(e)
        return False

async def shutdown_mr60bha2_integration():
    global mqtt_client
    try:
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            mqtt_client = None
        mr60bha2_status["connected"] = False
        logger.info("âœ… MR60BHA2 integration shutdown complete")
    except Exception as e:
        logger.error(f"âŒ Shutdown error: {e}")
