from pydantic import BaseModel, field_validator
from datetime import datetime

class PresenceEvent(BaseModel):
    user_id: str
    sensor_id: str
    confidence: float
    timestamp: datetime

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v
