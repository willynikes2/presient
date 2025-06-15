class MQTTClient:
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port

    def connect(self):
        pass

    def publish(self, topic, message):
        pass

    def subscribe(self, topic):
        pass

mqtt_client = MQTTClient("localhost", 1883)
