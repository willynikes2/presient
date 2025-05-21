from fastapi.testclient import TestClient
from backend.main import app
import datetime
import pytest

client = TestClient(app)


def test_presence_event(monkeypatch):
    published = {}

    def mock_publish(topic, payload):
        published['topic'] = topic
        published['payload'] = payload

    # Mock the mqtt_client.publish
    monkeypatch.setattr("backend.routes.presence.mqtt_client.publish", mock_publish)

    data = {
        "user_id": "user123",
        "sensor_id": "sensorABC",
        "confidence": 0.87,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    response = client.post("/presence/event", json=data)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert published["topic"] == "presient/presence/sensorABC"
