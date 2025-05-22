class MockMQTTClient:
    def publish(self, topic, payload):
        print(f"MQTT Publish: {topic} → {payload}")

<<<<<<< HEAD
mqtt_client = MockMQTTClient()
=======
mqtt_client = MockMQTTClient()
>>>>>>> d0aee7c15f003d5e9a37838a3fcd9bf4b258c668
