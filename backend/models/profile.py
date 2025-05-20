
from sqlalchemy import Column, Integer, String, Float
from db import Base

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    profile_vector = Column(String)  # Could be JSON or serialized vector
    label = Column(String)
