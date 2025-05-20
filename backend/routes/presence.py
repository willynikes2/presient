
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/report")
def report_presence(data: dict, db: Session = Depends(get_db)):
    # TODO: Add matching logic, MQTT publishing
    return {"status": "presence received", "data": data}
