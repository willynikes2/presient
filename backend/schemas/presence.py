from pydantic import BaseModel, Field
from datetime import datetime


class PresenceEvent(BaseModel):
    user_id: str
    sensor_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime

from pydantic import BaseModel
from datetime import datetime

class PresenceEventOut(BaseModel):
    id: str
    user_id: str
    sensor_id: str
    confidence: float
    timestamp: datetime

    class Config:
        # TODO: Convert to ConfigDict
        from_attributes = True
