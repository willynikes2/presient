
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models.sensor import Sensor
from schemas.sensor import SensorCreate, SensorOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SensorOut)
def create_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    db_sensor = Sensor(name=sensor.name, location=sensor.location)
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

@router.get("/", response_model=list[SensorOut])
def read_sensors(db: Session = Depends(get_db)):
    return db.query(Sensor).all()
