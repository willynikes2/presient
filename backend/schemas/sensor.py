
from pydantic import BaseModel

class SensorBase(BaseModel):
    name: str
    location: str

class SensorCreate(SensorBase):
    pass

class SensorOut(SensorBase):
    id: int
    is_online: bool

    class Config:
        # TODO: Convert to ConfigDict
        orm_mode = True
