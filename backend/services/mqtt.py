class MockMQTTClient:
    def publish(self, topic, payload):
        print(f"MQTT Publish: {topic} → {payload}")

mqtt_client = MockMQTTClient()
