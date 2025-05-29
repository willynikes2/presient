"""
Enhanced Profile routes with validation and additional features
Builds on your existing SQLAlchemy integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Dict, List, Any
import re
from datetime import datetime, timezone

# Your existing imports
from backend.schemas.profiles import ProfileCreate, ProfileUpdate, ProfileOut
from backend.models.profile import Profile
from backend.db.session import get_db

# Import from the new auth system
from backend.routes.auth import get_current_user

# Additional Pydantic models for new features
from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])

# ==================== Additional Pydantic Models ====================

class ProfileUpdateEnhanced(ProfileUpdate):
    """Enhanced profile update with validation"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class ProfilePreferences(BaseModel):
    """User preferences model"""
    theme: str = Field("light", pattern="^(light|dark|auto)$")
    language: str = Field("en", pattern="^[a-z]{2}(-[A-Z]{2})?$")
    timezone: str = Field("UTC", max_length=50)
    notifications: Dict[str, bool] = Field(default_factory=dict)
    
    @validator('notifications')
    def validate_notifications(cls, v):
        allowed_keys = ['email', 'push', 'sms', 'in_app']
        for key in v:
            if key not in allowed_keys:
                raise ValueError(f"Invalid notification type: {key}")
        return v

class ProfilePrivacy(BaseModel):
    """Profile privacy settings"""
    profile_visible: bool = True
    email_visible: bool = False
    location_visible: bool = True
    activity_visible: bool = True

class ProfileStats(BaseModel):
    """Profile statistics"""
    sensors_count: int = 0
    data_points: int = 0
    storage_used_mb: float = 0.0
    last_activity: Optional[datetime] = None

class ProfileWithStats(ProfileOut):
    """Profile response with optional statistics"""
    stats: Optional[ProfileStats] = None
    preferences: Optional[Dict[str, Any]] = None
    privacy: Optional[Dict[str, Any]] = None

# ==================== Helper Functions ====================

def validate_uuid(profile_id: UUID) -> UUID:
    """Validate UUID format"""
    # UUID type already validates format
    return profile_id

def check_profile_access(profile: Profile, current_user: Dict, check_privacy: bool = True) -> Profile:
    """Check if user has access to profile based on privacy settings"""
    is_own_profile = str(profile.user_id) == current_user["id"]
    
    if not is_own_profile and check_privacy:
        # Check privacy settings (assuming privacy is stored as JSON in profile)
        privacy = profile.privacy_settings or {}
        if not privacy.get("profile_visible", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "PROFILE_PRIVATE",
                    "message": "This profile is private"
                }
            )
    
    return profile

async def get_profile_stats(profile_id: UUID, db: Session) -> ProfileStats:
    """Get profile statistics - implement based on your data model"""
    # TODO: Implement actual statistics queries
    # Example:
    # sensors_count = db.query(Sensor).filter(Sensor.user_id == profile_id).count()
    # data_points = db.query(DataPoint).filter(DataPoint.user_id == profile_id).count()
    
    return ProfileStats(
        sensors_count=5,
        data_points=1234,
        storage_used_mb=45.7,
        last_activity=datetime.now(timezone.utc)
    )

# ==================== Enhanced Routes ====================

# Keep your existing create route
@router.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile: ProfileCreate, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new profile - enhanced with current user validation"""
    # Check if profile already exists for user
    existing = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "PROFILE_EXISTS",
                "message": "Profile already exists for this user"
            }
        )
    
    new_profile = Profile(**profile.model_dump(), user_id=current_user["id"])
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

# Enhanced list profiles with pagination
@router.get("/", response_model=List[ProfileOut])
def list_profiles(
    skip: int = Query(0, ge=0, description="Number of profiles to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of profiles to return"),
    include_private: bool = Query(False, description="Include private profiles"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List profiles with pagination and privacy filtering"""
    query = db.query(Profile)
    
    if not include_private:
        # Filter out private profiles (assuming privacy_settings is JSON)
        # This is a simplified version - adjust based on your actual schema
        query = query.filter(
            Profile.privacy_settings['profile_visible'].astext == 'true'
        )
    
    profiles = query.offset(skip).limit(limit).all()
    return profiles

# Enhanced get profile with stats and privacy
@router.get("/search", response_model=List[ProfileOut])
def search_profiles(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Search profiles by name, bio, or location"""
    # Search in full_name, bio, and location
    # This is a simple implementation - consider using full-text search in production
    search_pattern = f"%{q}%"
    
    profiles = db.query(Profile).filter(
        (Profile.full_name.ilike(search_pattern)) |
        (Profile.bio.ilike(search_pattern)) |
        (Profile.location.ilike(search_pattern))
    ).filter(
        # Only show public profiles
        Profile.privacy_settings['profile_visible'].astext == 'true'
    ).limit(limit).all()
    
    return profiles
# ==================== /me routes (must come before /{profile_id}) ====================

@router.get("/me", response_model=ProfileWithStats)
async def get_my_profile(
    include_stats: bool = Query(True, description="Include usage statistics"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get current user's profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    
    if not profile:
        # Auto-create profile if it doesn't exist
        profile = Profile(
            user_id=current_user["id"],
            email=current_user["email"],
            name=current_user.get("full_name", current_user.get("username", "User")),  # Use full_name or username for name
            full_name=current_user.get("full_name"),
            preferences={},
            privacy_settings=ProfilePrivacy().model_dump()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    response = ProfileWithStats.from_orm(profile)
    
    if include_stats:
        response.stats = await get_profile_stats(profile.id, db)
    
    return response

# Enhanced update with validation
@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    updates: ProfileUpdateEnhanced,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update current user's profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PROFILE_NOT_FOUND",
                "message": "Profile not found. Create one first."
            }
        )
    
    return update_profile(profile.id, updates, db, current_user)

# New route for preferences
@router.put("/me/preferences", response_model=Dict[str, Any])
def update_preferences(
    preferences: ProfilePreferences,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update user preferences"""
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PROFILE_NOT_FOUND"}
        )
    
    # Update preferences (assuming it's a JSON column)
    profile.preferences = preferences.model_dump()
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "status": "success",
        "message": "Preferences updated successfully",
        "preferences": profile.preferences
    }

# New route for privacy settings
@router.put("/me/privacy", response_model=Dict[str, Any])
def update_privacy_settings(
    privacy: ProfilePrivacy,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update privacy settings"""
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PROFILE_NOT_FOUND"}
        )
    
    # Update privacy settings (assuming it's a JSON column)
    profile.privacy_settings = privacy.model_dump()
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "status": "success",
        "message": "Privacy settings updated successfully",
        "privacy": profile.privacy_settings
    }

# New route for avatar upload
@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Upload profile avatar"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_FILE_TYPE",
                "message": f"File type '{file.content_type}' not allowed",
                "allowed_types": allowed_types
            }
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "FILE_TOO_LARGE",
                "message": f"File size exceeds maximum of 5MB",
                "size": len(file_content),
                "max_size": max_size
            }
        )
    
    # Get profile
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PROFILE_NOT_FOUND"}
        )
    
    # TODO: Save file to storage (S3, local, etc.)
    # For now, just save the filename
    avatar_url = f"/avatars/{current_user['id']}/{file.filename}"
    
    # Update profile
    profile.avatar_url = avatar_url
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "status": "success",
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }

# Enhanced delete with ownership check

# ==================== /{profile_id} routes ====================

@router.get("/{profile_id}", response_model=ProfileWithStats)
async def get_profile(
    profile_id: UUID,
    include_stats: bool = Query(False, description="Include usage statistics"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get profile with privacy checks and optional statistics"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        # Check if this is a user ID instead of profile ID
        profile = db.query(Profile).filter(Profile.user_id == profile_id).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "PROFILE_NOT_FOUND",
                    "profile_id": str(profile_id),
                    "message": "Profile not found",
                    "suggestion": "Check the profile ID or create a profile first"
                }
            )
    
    # Check access permissions
    profile = check_profile_access(profile, current_user)
    
    # Convert to response model
    response = ProfileWithStats.from_orm(profile)
    
    # Add stats if requested
    if include_stats:
        response.stats = await get_profile_stats(profile.id, db)
    
    # Filter sensitive data if not own profile
    is_own_profile = str(profile.user_id) == current_user["id"]
    if not is_own_profile:
        privacy = profile.privacy_settings or {}
        if not privacy.get("email_visible", False):
            response.email = None
        if not privacy.get("location_visible", True):
            response.location = None
    
    return response

# Get current user's profile
@router.put("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: UUID,
    updates: ProfileUpdateEnhanced,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update profile with enhanced validation and ownership check"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PROFILE_NOT_FOUND",
                "profile_id": str(profile_id),
                "message": "Profile not found"
            }
        )
    
    # Check ownership
    if str(profile.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "NOT_AUTHORIZED",
                "message": "You can only update your own profile"
            }
        )
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NO_UPDATES",
                "message": "No fields to update"
            }
        )
    
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    return profile

# Update own profile (simpler endpoint)
@router.delete("/{profile_id}", response_model=Dict[str, str])
def delete_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Delete profile with ownership validation"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PROFILE_NOT_FOUND",
                "profile_id": str(profile_id),
                "message": "Profile not found"
            }
        )
    
    # Check ownership
    if str(profile.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "NOT_AUTHORIZED",
                "message": "You can only delete your own profile"
            }
        )
    
    db.delete(profile)
    db.commit()
    
    return {
        "status": "success",
        "message": "Profile deleted successfully"
    }

# Search profiles
