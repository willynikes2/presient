import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db import Base

class PresenceEvent(Base):
    __tablename__ = "presence_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.id"), index=True)  # ✅ Restored FK
    sensor_id = Column(String, index=True)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship to Profile
    profile = relationship("Profile", back_populates="presence_events")
