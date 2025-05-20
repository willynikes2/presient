
from sqlalchemy import Column, Integer, String, Boolean
from db import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    is_online = Column(Boolean, default=False)
