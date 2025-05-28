from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.base import Base
import uuid
from datetime import datetime

class PresenceEvent(Base):
    __tablename__ = "presence_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.user_id"), nullable=False)  # ForeignKey link
    sensor_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="presence_events")
