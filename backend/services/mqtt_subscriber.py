"""
MR60BHA2 MQTT Subscriber Service for Presient Backend
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

mqtt_client = None
mr60bha2_status = {
    "connected": False,
    "last_heartbeat": None,
    "last_error": None,
    "heart_rate_buffer": [],
    "presence_detected": False
}

def get_mr60bha2_status() -> Dict[str, Any]:
    """Get current MR60BHA2 sensor status"""
    return {
        "status": "connected" if mr60bha2_status["connected"] else "disconnected",
        "last_heartbeat": mr60bha2_status["last_heartbeat"],
        "heart_rate_samples": len(mr60bha2_status["heart_rate_buffer"]),
        "presence": mr60bha2_status["presence_detected"],
        "last_error": mr60bha2_status["last_error"]
    }

async def startup_mr60bha2_integration(mqtt_service=None):
    """Initialize MR60BHA2 MQTT integration"""
    global mqtt_client, mr60bha2_status
    
    try:
        logger.info("🔄 Starting MR60BHA2 MQTT integration...")
        
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning("⚠️ paho-mqtt not installed.")
            mr60bha2_status["last_error"] = "paho-mqtt not installed"
            return False
        
        logger.info("✅ MR60BHA2 integration initialized (mock)")
        mr60bha2_status["connected"] = True
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MR60BHA2 integration: {e}")
        mr60bha2_status["last_error"] = str(e)
        return False

async def shutdown_mr60bha2_integration():
    """Clean shutdown of MR60BHA2 integration"""
    global mqtt_client, mr60bha2_status
    
    try:
        logger.info("✅ MR60BHA2 integration shutdown complete")
        mr60bha2_status["connected"] = False
        
    except Exception as e:
        logger.error(f"❌ Error during MR60BHA2 shutdown: {e}")