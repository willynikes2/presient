from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from backend.schemas.profiles import ProfileCreate, ProfileUpdate, ProfileOut
from backend.models.profile import Profile
from backend.db.session import get_db

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("/", response_model=ProfileOut)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    new_profile = Profile(**profile.dict())
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@router.get("/", response_model=list[ProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(Profile).all()


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: UUID, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: UUID, updates: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", response_model=dict)
def delete_profile(profile_id: UUID, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted"}
