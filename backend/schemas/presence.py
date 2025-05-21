from pydantic import BaseModel, Field
from datetime import datetime


class PresenceEvent(BaseModel):
    user_id: str
    sensor_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
