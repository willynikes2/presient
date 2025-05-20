
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import SessionLocal
from models.profile import Profile
from schemas.profile import ProfileCreate, ProfileOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProfileOut)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    db_profile = Profile(**profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile
