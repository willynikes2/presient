
from pydantic import BaseModel

class ProfileCreate(BaseModel):
    user_id: str
    profile_vector: str
    label: str

class ProfileOut(ProfileCreate):
    id: int

    class Config:
        orm_mode = True
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProfileBase(BaseModel):
    name: str
    heartbeat_signature: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True