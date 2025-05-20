
from pydantic import BaseModel

class ProfileCreate(BaseModel):
    user_id: str
    profile_vector: str
    label: str

class ProfileOut(ProfileCreate):
    id: int

    class Config:
        orm_mode = True
