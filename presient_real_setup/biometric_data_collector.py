#!/usr/bin/env python3
"""
Biometric Data Collector - Collects heart rate data for enrollment
Compatible with paho-mqtt v2.0+ and multi-user enrollment
"""

import paho.mqtt.client as mqtt
import time
import statistics
from datetime import datetime
from typing import List
import logging

try:
    from real_biometric_matcher import BiometricSample
except ImportError:
    print("⚠️ Could not import BiometricSample — make sure real_biometric_matcher.py is available.")
    BiometricSample = None

logger = logging.getLogger(__name__)

class BiometricDataCollector:
    """Collect biometric data from MR60BHA2 sensor for enrollment"""
    
    def __init__(self, mqtt_host="192.168.1.135", mqtt_port=1883, topic="presient/sensor1/heart_rate/state"):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.topic = topic
        self.collected_samples = []
        self.collection_seconds = 60  # Increased to 60 seconds for better data
        self._client = None
        self._start_time = None
        self.is_collecting = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT connection callback - compatible with paho-mqtt v2.0+"""
        if rc == 0:
            print("✅ MQTT connected")
            # Subscribe to multiple heart rate topics
            topics = [
                "presient/sensor1/heart_rate/state",
                "presient/sensor1/sensor/presient_mr60bha2_sensor_heart_rate/state",
                "presient/sensor1/breath_rate/state",
                "presient/sensor1/sensor/presient_mr60bha2_sensor_breathing_rate/state"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.debug(f"📡 Subscribed to: {topic}")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")

    def _on_message(self, client, userdata, message, properties=None):
        """MQTT message callback - compatible with paho-mqtt v2.0+"""
        if not self.is_collecting or not BiometricSample:
            return
            
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')
            
            # Process heart rate data
            if "heart_rate" in topic and "/state" in topic:
                heart_rate = float(payload)
                
                # Validate heart rate (skip fallback values)
                if 40 <= heart_rate <= 180 and heart_rate != 40.0:
                    sample = BiometricSample(
                        heart_rate=heart_rate,
                        timestamp=datetime.now()
                    )
                    self.collected_samples.append(sample)
                    print(f"💓 Sampled: {heart_rate} BPM (#{len(self.collected_samples)})")
                    
            # Process breathing rate data
            elif ("breath_rate" in topic or "breathing_rate" in topic) and "/state" in topic:
                try:
                    breathing_rate = float(payload)
                    # Add to most recent sample if it exists and doesn't have breathing rate
                    if (self.collected_samples and 
                        self.collected_samples[-1].breathing_rate is None and
                        (datetime.now() - self.collected_samples[-1].timestamp).total_seconds() < 5):
                        self.collected_samples[-1].breathing_rate = breathing_rate
                        logger.debug(f"🫁 Added breathing: {breathing_rate:.1f} BPM")
                except ValueError:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Failed to parse MQTT message: {e}")

    def collect_enrollment_data(self, user_name: str) -> List[BiometricSample]:
        """Collect biometric data for user enrollment"""
        print(f"🧪 Collecting {self.collection_seconds} seconds of heart rate data for {user_name}...")
        print("📍 Please stay near your MR60BHA2 sensor...")

        self.collected_samples.clear()
        self.is_collecting = True
        self._start_time = datetime.now()
        
        # Create MQTT client with v2.0+ compatibility
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "presient_enrollment_collector")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        try:
            self._client.connect(self.mqtt_host, self.mqtt_port, 60)
            self._client.loop_start()

            # Collect for specified duration with progress updates
            start_time = time.time()
            while time.time() - start_time < self.collection_seconds:
                remaining = self.collection_seconds - (time.time() - start_time)
                if remaining > 0:
                    if len(self.collected_samples) == 0:
                        print(f"⏳ Waiting for sensor data... ({remaining:.0f}s remaining)")
                    elif len(self.collected_samples) % 10 == 0 and len(self.collected_samples) > 0:
                        print(f"📊 Collected {len(self.collected_samples)} samples ({remaining:.0f}s remaining)")
                    time.sleep(1)

        finally:
            self.is_collecting = False
            self._client.loop_stop()
            self._client.disconnect()

        print(f"✅ Finished collecting {len(self.collected_samples)} samples")
        
        # Show statistics if we have enough data
        if len(self.collected_samples) >= 5:
            heart_rates = [s.heart_rate for s in self.collected_samples]
            print(f"📊 Heart Rate Statistics:")
            print(f"   💓 Average: {statistics.mean(heart_rates):.1f} BPM")
            print(f"   📈 Range: {min(heart_rates):.1f} - {max(heart_rates):.1f} BPM")
            print(f"   📊 Std Dev: {statistics.stdev(heart_rates):.1f} BPM")
            
            breathing_rates = [s.breathing_rate for s in self.collected_samples if s.breathing_rate]
            if breathing_rates:
                print(f"   🫁 Breathing: {statistics.mean(breathing_rates):.1f} BPM avg")
        
        return self.collected_samples

