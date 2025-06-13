"""
MR60BHA2 MQTT Subscriber Service for Presient Backend
Connects to Home Assistant MQTT and processes real heart rate data
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(**name**)

# Global variables for service state

mqtt\_client = None
mr60bha2\_status = {
"connected": False,
"last\_heartbeat": None,
"last\_error": None,
"heart\_rate\_buffer": \[],
"presence\_detected": False
}

def get\_mr60bha2\_status() -> Dict\[str, Any]:
"""Get current MR60BHA2 sensor status"""
return {
"status": "connected" if mr60bha2\_status\["connected"] else "disconnected",
"last\_heartbeat": mr60bha2\_status\["last\_heartbeat"],
"heart\_rate\_samples": len(mr60bha2\_status\["heart\_rate\_buffer"]),
"presence": mr60bha2\_status\["presence\_detected"],
"last\_error": mr60bha2\_status\["last\_error"]
}

async def startup\_mr60bha2\_integration(mqtt\_service=None):
"""
Initialize MR60BHA2 MQTT integration

```
Args:
    mqtt_service: Optional MQTT service instance
"""
global mqtt_client, mr60bha2_status

try:
    logger.info("🔄 Starting MR60BHA2 MQTT integration...")

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("⚠️ paho-mqtt not installed. MR60BHA2 integration disabled.")
        logger.info("💡 Install with: pip install paho-mqtt")
        mr60bha2_status["last_error"] = "paho-mqtt not installed"
        return False

    mqtt_client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Connected to MQTT broker for MR60BHA2 data")
            mr60bha2_status["connected"] = True
            mr60bha2_status["last_error"] = None

            topics = [
                "homeassistant/sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_heart_rate/state",
                "homeassistant/sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_breathing_rate/state",
                "homeassistant/binary_sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_presence/state"
            ]

            for topic in topics:
                client.subscribe(topic)
                logger.debug(f"📡 Subscribed to: {topic}")
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
            mr60bha2_status["connected"] = False
            mr60bha2_status["last_error"] = f"MQTT connection failed: {rc}"

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logger.debug(f"📨 MQTT message: {topic} = {payload}")

            if "heart_rate/state" in topic:
                try:
                    heart_rate = float(payload)
                    if 40 <= heart_rate <= 180:
                        mr60bha2_status["heart_rate_buffer"].append({
                            "value": heart_rate,
                            "timestamp": datetime.now().isoformat()
                        })
                        if len(mr60bha2_status["heart_rate_buffer"]) > 30:
                            mr60bha2_status["heart_rate_buffer"].pop(0)
                        mr60bha2_status["last_heartbeat"] = datetime.now().isoformat()
                        logger.info(f"💓 Heart rate detected: {heart_rate} BPM")
                except ValueError:
                    logger.debug(f"Invalid heart rate value: {payload}")

            elif "presence/state" in topic:
                mr60bha2_status["presence_detected"] = payload.lower() in ["on", "true", "1"]
                logger.info(f"👤 Presence: {'detected' if mr60bha2_status['presence_detected'] else 'cleared'}")

        except Exception as e:
            logger.error(f"❌ Error processing MQTT message: {e}")
            mr60bha2_status["last_error"] = str(e)

    def on_disconnect(client, userdata, rc):
        logger.warning(f"⚠️ Disconnected from MQTT broker: {rc}")
        mr60bha2_status["connected"] = False

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    try:
        mqtt_client.connect("192.168.1.102", 1883, 60)
        mqtt_client.loop_start()
        logger.info("🚀 MR60BHA2 MQTT integration started")
        return True
    except Exception as e:
        logger.error(f"❌ Could not connect to MQTT broker: {e}")
        mr60bha2_status["last_error"] = str(e)
        return False

except Exception as e:
    logger.error(f"❌ Failed to initialize MR60BHA2 integration: {e}")
    mr60bha2_status["last_error"] = str(e)
    return False
```

async def shutdown\_mr60bha2\_integration():
"""Clean shutdown of MR60BHA2 integration"""
global mqtt\_client, mr60bha2\_status

```
try:
    if mqtt_client:
        logger.info("🔄 Shutting down MR60BHA2 MQTT integration...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None

    mr60bha2_status["connected"] = False
    logger.info("✅ MR60BHA2 integration shutdown complete")

except Exception as e:
    logger.error(f"❌ Error during MR60BHA2 shutdown: {e}")
```
