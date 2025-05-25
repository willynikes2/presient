# backend/models/presence_events.py
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.db.base import Base
import uuid
from datetime import datetime

class PresenceEvent(Base):
    __tablename__ = "presence_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    sensor_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Define the reverse relationship to Profile
    profile = relationship("Profile", back_populates="presence_events")