#!/usr/bin/env python3
"""
Integrate Biometric Matching with Backend MQTT Subscriber
Adds real biometric matching to the existing backend
"""

import os
import sys
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_existing_subscriber():
    """Backup the current MQTT subscriber"""
    backend_dir = "/mnt/c/dev/presient/presient/backend"
    subscriber_file = os.path.join(backend_dir, "services", "mqtt_subscriber.py")
    
    if os.path.exists(subscriber_file):
        backup_file = subscriber_file + ".backup"
        shutil.copy2(subscriber_file, backup_file)
        logger.info(f"✅ Backed up existing subscriber: {backup_file}")
        return True
    else:
        logger.error(f"❌ Subscriber file not found: {subscriber_file}")
        return False

def integrate_biometric_matching():
    """Add biometric matching to the backend MQTT subscriber"""
    
    enhanced_subscriber_code = '''"""
Enhanced MR60BHA2 MQTT Subscriber with Real Biometric Matching
Processes heart rate data and performs biometric authentication
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import statistics

# Add the setup directory to path for biometric matcher
setup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "presient_real_setup")
if os.path.exists(setup_dir):
    sys.path.append(setup_dir)
    try:
        from real_biometric_matcher import RealBiometricMatcher, BiometricSample
        BIOMETRIC_MATCHER_AVAILABLE = True
        logger.info("✅ Biometric matcher imported successfully")
    except ImportError as e:
        BIOMETRIC_MATCHER_AVAILABLE = False
        logger.warning(f"⚠️ Biometric matcher not available: {e}")
else:
    BIOMETRIC_MATCHER_AVAILABLE = False
    logger.warning("⚠️ Setup directory not found - biometric matching disabled")

logger = logging.getLogger("backend.services.mqtt_subscriber")

# Global service state
mqtt_client = None
mr60bha2_status = {
    "connected": False,
    "last_heartbeat": None,
    "last_error": None,
    "heart_rate_buffer": [],
    "presence_detected": False,
    "biometric_matches": 0,
    "last_match_time": None
}

# Biometric matching components
biometric_matcher = None
automation_settings = {}

def get_mr60bha2_status() -> Dict[str, Any]:
    return {
        "connected": mr60bha2_status["connected"],
        "last_heartbeat": mr60bha2_status["last_heartbeat"],
        "buffer_size": len(mr60bha2_status["heart_rate_buffer"]),
        "presence_detected": mr60bha2_status["presence_detected"],
        "biometric_matches": mr60bha2_status["biometric_matches"],
        "last_match_time": mr60bha2_status["last_match_time"],
        "topics_subscribed": 6,
        "module_available": BIOMETRIC_MATCHER_AVAILABLE,
        "topics": [
            "presient/sensor1/heart_rate/state",
            "presient/sensor1/breath_rate/state", 
            "presient/sensor1/presence/state",
            "presient/sensor1/sensor/presient_mr60bha2_sensor_heart_rate/state",
            "presient/sensor1/sensor/presient_mr60bha2_sensor_breathing_rate/state",
            "homeassistant/sensor/presient-sensor-1-b4b93c/presient_mr60bha2_sensor_heart_rate/state"
        ],
        "last_error": mr60bha2_status["last_error"]
    }

async def startup_mr60bha2_integration(biometric=None, automation=None):
    global mqtt_client, biometric_matcher, automation_settings

    if automation:
        automation_settings = automation

    # Initialize biometric matcher if available
    if BIOMETRIC_MATCHER_AVAILABLE:
        try:
            biometric_matcher = RealBiometricMatcher()
            logger.info(f"✅ Biometric matcher initialized with {len(biometric_matcher.profiles)} profiles")
        except Exception as e:
            logger.error(f"❌ Failed to initialize biometric matcher: {e}")
            biometric_matcher = None

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("⚠️ paho-mqtt not installed.")
        mr60bha2_status["last_error"] = "paho-mqtt not installed"
        return False

    mqtt_client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Connected to MQTT broker")
            mr60bha2_status["connected"] = True
            for topic in get_mr60bha2_status()["topics"]:
                client.subscribe(topic)
                logger.debug(f"📡 Subscribed to: {topic}")
        else:
            logger.error(f"❌ MQTT connection failed: {rc}")
            mr60bha2_status["last_error"] = f"Connection failed: {rc}"

    def on_message(client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        logger.debug(f"MQTT Message: {topic} = {payload}")
        
        try:
            if "heart_rate/state" in topic:
                heart_rate = float(payload)
                if 40 <= heart_rate <= 180:
                    # Store in buffer
                    mr60bha2_status["heart_rate_buffer"].append({
                        "value": heart_rate,
                        "timestamp": datetime.now().isoformat()
                    })
                    if len(mr60bha2_status["heart_rate_buffer"]) > 30:
                        mr60bha2_status["heart_rate_buffer"].pop(0)
                    mr60bha2_status["last_heartbeat"] = datetime.now().isoformat()
                    logger.info(f"❤️ Heart rate: {heart_rate} BPM")
                    
                    # **NEW: Biometric Matching**
                    if biometric_matcher and heart_rate != 40.0:  # Skip fallback values
                        try:
                            # Add sample to matcher
                            sample = BiometricSample(
                                heart_rate=heart_rate,
                                timestamp=datetime.now()
                            )
                            biometric_matcher.add_sample(sample)
                            
                            # Try to find a match
                            match_result = biometric_matcher.find_best_match(
                                presence_detected=mr60bha2_status["presence_detected"]
                            )
                            
                            if match_result and match_result.confidence >= 0.75:
                                logger.info(f"🎯 REAL MATCH: {match_result.name} ({match_result.confidence:.1%})")
                                mr60bha2_status["biometric_matches"] += 1
                                mr60bha2_status["last_match_time"] = datetime.now().isoformat()
                                
                                # TODO: Send push notification here
                                logger.info("🔔 Ring-style notification triggered!")
                                
                            else:
                                logger.debug(f"🤔 No confident match for HR: {heart_rate} BPM")
                                
                        except Exception as e:
                            logger.error(f"❌ Biometric matching error: {e}")

            elif "breathing_rate/state" in topic or "breath_rate/state" in topic:
                try:
                    breathing_rate = float(payload)
                    # Add to latest biometric sample if available
                    if (biometric_matcher and biometric_matcher.recent_samples and 
                        biometric_matcher.recent_samples[-1].breathing_rate is None):
                        biometric_matcher.recent_samples[-1].breathing_rate = breathing_rate
                        logger.debug(f"🫁 Breathing: {breathing_rate} BPM")
                except ValueError:
                    pass

            elif "presence/state" in topic:
                mr60bha2_status["presence_detected"] = payload.lower() in ["on", "true", "1"]
                presence = 'detected' if mr60bha2_status["presence_detected"] else 'cleared'
                logger.info(f"🧍 Presence: {presence}")

        except Exception as e:
            logger.error(f"❌ Error in on_message: {e}")
            mr60bha2_status["last_error"] = str(e)

    def on_disconnect(client, userdata, rc):
        logger.warning(f"⚠️ MQTT disconnected: {rc}")
        mr60bha2_status["connected"] = False

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    # Use env or default
    broker_host = os.getenv("MQTT_BROKER_HOST", "192.168.1.135")

    try:
        mqtt_client.connect(broker_host, 1883, 60)
        mqtt_client.loop_start()
        logger.info("🚀 Enhanced MR60BHA2 MQTT integration with biometric matching running")
        return True
    except Exception as e:
        logger.error(f"❌ MQTT connection exception: {e}")
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
        logger.info("✅ Enhanced MR60BHA2 integration shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
'''
    
    # Write the enhanced subscriber
    backend_dir = "/mnt/c/dev/presient/presient/backend"
    subscriber_file = os.path.join(backend_dir, "services", "mqtt_subscriber.py")
    
    try:
        with open(subscriber_file, "w") as f:
            f.write(enhanced_subscriber_code)
        logger.info("✅ Enhanced MQTT subscriber with biometric matching created")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to write subscriber: {e}")
        return False

def main():
    """Main integration process"""
    logger.info("🔧 Integrating Biometric Matching with Backend")
    logger.info("=" * 50)
    
    # Step 1: Backup existing subscriber
    if not backup_existing_subscriber():
        logger.error("❌ Failed to backup subscriber")
        return False
    
    # Step 2: Integrate biometric matching
    if not integrate_biometric_matching():
        logger.error("❌ Failed to integrate biometric matching")
        return False
    
    logger.info("\n✅ Integration complete!")
    logger.info("\nNext steps:")
    logger.info("1. Restart your Presient backend")
    logger.info("2. You should see biometric matching in logs")
    logger.info("3. Walk near your sensor to test!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Ready to test! Restart your backend and approach your sensor!")
    else:
        print("\n❌ Integration failed. Check the logs above.")