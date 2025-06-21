#!/usr/bin/env python3
"""
Biometric Data Collector - Collects heart rate data for enrollment
"""

import paho.mqtt.client as mqtt
import time
from datetime import datetime

try:
    from real_biometric_matcher import BiometricSample
except ImportError:
    print("⚠️ Could not import BiometricSample — make sure real_biometric_matcher.py is available.")
    BiometricSample = None

class BiometricDataCollector:
    def __init__(self, mqtt_host="localhost", mqtt_port=1883, topic="presient/sensor1/heart_rate/state"):
        self.mqtt_host = "192.168.1.135"
        self.mqtt_port = mqtt_port
        self.topic = topic
        self.collected_samples = []
        self.collection_seconds = 60
        self._client = None
        self._start_time = None

    # Made 'properties' optional by giving it a default value of None
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ MQTT connected")
            client.subscribe(self.topic)
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")

    # Made 'properties' optional by giving it a default value of None
    def _on_message(self, client, userdata, message, properties=None):
        if not self._start_time or not BiometricSample:
            return
        try:
            heart_rate = float(message.payload.decode())
            sample = BiometricSample(heart_rate=heart_rate, timestamp=datetime.now())
            self.collected_samples.append(sample)
            print(f"💓 Sampled: {heart_rate} BPM")
        except Exception as e:
            print(f"⚠️ Failed to parse MQTT message: {e}")

    def collect_enrollment_data(self, user_name: str):
        print(f"🧪 Collecting {self.collection_seconds} seconds of heart rate data for {user_name}...")

        self.collected_samples.clear()
        self._start_time = datetime.now()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "presient_enrollment_collector")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        try:
            self._client.connect(self.mqtt_host, self.mqtt_port, 60)
            self._client.loop_start()

            time.sleep(self.collection_seconds)

        finally:
            self._client.loop_stop()
            self._client.disconnect()

        print(f"✅ Finished collecting {len(self.collected_samples)} samples")
        return self.collected_samples
