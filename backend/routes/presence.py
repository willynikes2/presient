from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import json
import uuid
from backend.schemas.presence import PresenceEvent, PresenceEventOut
from backend.db import get_db
from backend.models.presence_events import PresenceEvent as PresenceEventModel
from backend.services.mqtt import mqtt_client

router = APIRouter()

@router.post("/presence/event")
async def presence_event(event: PresenceEvent, db: Session = Depends(get_db)):
    print(
        f"User {event.user_id} detected by {event.sensor_id} "
        f"with {event.confidence * 100:.2f}% confidence at {event.timestamp}"
    )

    new_event = PresenceEventModel(
        id=str(uuid.uuid4()),
        user_id=event.user_id,
        sensor_id=event.sensor_id,
        confidence=event.confidence,
        timestamp=event.timestamp,
    )
    db.add(new_event)
    db.commit()

    topic = f"presient/presence/{event.sensor_id}"
    payload = json.dumps({
        "user_id": event.user_id,
        "confidence": event.confidence,
        "timestamp": event.timestamp.isoformat(),
    })
    mqtt_client.publish(topic, payload)

    return {"status": "ok"}


@router.get("/presence/events", response_model=List[PresenceEventOut])
def list_presence_events(db: Session = Depends(get_db)):
    return db.query(PresenceEventModel).all()
