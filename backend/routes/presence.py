from fastapi import APIRouter
from backend.schemas.presence import PresenceEvent
from backend.services.mqtt import mqtt_client
import json

router = APIRouter()

@router.post("/presence/event")
async def presence_event(event: PresenceEvent):
    print(f"User {event.user_id} detected by {event.sensor_id} with {event.confidence:.2%} confidence at {event.timestamp}")
    payload = json.dumps(event.model_dump(), default=str)
    mqtt_client.publish(f"presient/presence/{event.sensor_id}", payload)
    return {"status": "ok"}
