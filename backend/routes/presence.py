from fastapi import APIRouter
from backend.schemas.presence import PresenceEvent
import json
from backend.services.mqtt import mqtt_client

router = APIRouter()

@router.post("/presence/event")
async def presence_event(event: PresenceEvent):
    # Log the event
    print(
        f"User {event.user_id} detected by {event.sensor_id} "
        f"with {event.confidence * 100:.2f}% confidence at {event.timestamp.isoformat()}"
    )

    # Publish to MQTT
    topic = f"presient/presence/{event.sensor_id}"
    payload = json.dumps(event.model_dump(), default=str)

    mqtt_client.publish(topic, payload)

    return {"status": "ok"}
