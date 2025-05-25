"""
Enhanced Profile Schemas matching the new Profile model
Supports all features: auth integration, preferences, privacy, presence
"""

from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
import re

# ==================== Base Schemas ====================

class ProfileBase(BaseModel):
    """Base profile schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    heartbeat_signature: Optional[str] = None
    
    # Additional profile fields
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('username')
    def validate_username(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower() if v else v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

# ==================== Preferences & Privacy Schemas ====================

class NotificationPreferences(BaseModel):
    """Notification preferences"""
    email: bool = True
    push: bool = True
    sms: bool = False
    in_app: bool = True

class ProfilePreferences(BaseModel):
    """User preferences schema"""
    theme: str = Field("light", regex="^(light|dark|auto)$")
    language: str = Field("en", regex="^[a-z]{2}(-[A-Z]{2})?$")
    timezone: str = Field("UTC", max_length=50)
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    
    class Config:
        json_schema_extra = {
            "example": {
                "theme": "dark",
                "language": "en-US",
                "timezone": "America/New_York",
                "notifications": {
                    "email": True,
                    "push": True,
                    "sms": False,
                    "in_app": True
                }
            }
        }

class ProfilePrivacy(BaseModel):
    """Profile privacy settings"""
    profile_visible: bool = True
    email_visible: bool = False
    location_visible: bool = True
    activity_visible: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_visible": True,
                "email_visible": False,
                "location_visible": True,
                "activity_visible": True
            }
        }

# ==================== Create/Update Schemas ====================

class ProfileCreate(ProfileBase):
    """Schema for creating a new profile"""
    user_id: Optional[UUID] = None  # Will be set from authenticated user
    preferences: Optional[ProfilePreferences] = Field(default_factory=ProfilePreferences)
    privacy_settings: Optional[ProfilePrivacy] = Field(default_factory=ProfilePrivacy)

class ProfileUpdate(BaseModel):
    """Schema for updating profile - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    heartbeat_signature: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower() if v else v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

# ==================== Response Schemas ====================

class ProfileStats(BaseModel):
    """Profile statistics"""
    sensors_count: int = 0
    data_points: int = 0
    storage_used_mb: float = 0.0
    last_activity: Optional[datetime] = None

class ProfilePresenceInfo(BaseModel):
    """Current presence information"""
    online_status: str = Field("offline", regex="^(online|away|busy|offline)$")
    custom_status_message: Optional[str] = None
    last_known_location: Optional[str] = None
    last_location_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    last_presence_event: Optional[datetime] = None

class ProfileOut(ProfileBase):
    """Profile response schema"""
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Settings (only included for own profile or based on privacy)
    preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    
    # Status
    is_active: bool = True
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProfileWithStats(ProfileOut):
    """Profile with optional statistics"""
    stats: Optional[ProfileStats] = None

class ProfileWithPresence(ProfileOut):
    """Profile with presence information"""
    presence: ProfilePresenceInfo = Field(default_factory=ProfilePresenceInfo)

class ProfileComplete(ProfileOut):
    """Complete profile with all information (for profile owner)"""
    stats: Optional[ProfileStats] = None
    presence: ProfilePresenceInfo = Field(default_factory=ProfilePresenceInfo)
    preferences: ProfilePreferences = Field(default_factory=ProfilePreferences)
    privacy_settings: ProfilePrivacy = Field(default_factory=ProfilePrivacy)

# ==================== List/Search Schemas ====================

class ProfileListResponse(BaseModel):
    """Response for profile list endpoints"""
    profiles: List[ProfileOut]
    total: int
    page: int = 1
    per_page: int = 100
    has_more: bool = False

class ProfileSearchResult(BaseModel):
    """Search result item"""
    id: UUID
    name: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    match_score: Optional[float] = None

# ==================== Special Update Schemas ====================

class PreferencesUpdate(BaseModel):
    """Update only preferences"""
    theme: Optional[str] = Field(None, regex="^(light|dark|auto)$")
    language: Optional[str] = Field(None, regex="^[a-z]{2}(-[A-Z]{2})?$")
    timezone: Optional[str] = Field(None, max_length=50)
    notifications: Optional[Dict[str, bool]] = None
    
    @validator('notifications')
    def validate_notifications(cls, v):
        if v:
            allowed_keys = ['email', 'push', 'sms', 'in_app']
            for key in v:
                if key not in allowed_keys:
                    raise ValueError(f"Invalid notification type: {key}")
        return v

class PrivacyUpdate(BaseModel):
    """Update only privacy settings"""
    profile_visible: Optional[bool] = None
    email_visible: Optional[bool] = None
    location_visible: Optional[bool] = None
    activity_visible: Optional[bool] = None

class PresenceStatusUpdate(BaseModel):
    """Update online status"""
    status: str = Field(..., regex="^(online|away|busy|offline)$")
    custom_message: Optional[str] = Field(None, max_length=100)

# ==================== Legacy Support ====================

# Keep this for backward compatibility with vector-based profiles if needed
class ProfileVectorCreate(BaseModel):
    """Legacy schema for vector-based profile creation"""
    user_id: str
    profile_vector: str
    label: str

class ProfileVectorOut(ProfileVectorCreate):
    """Legacy schema for vector-based profile response"""
    id: int
    
    class Config:
        orm_mode = True

# ==================== Examples ====================
"""
Example usage:

# Create a new profile
create_data = ProfileCreate(
    name="John Doe",
    username="johndoe",
    email="john@example.com",
    bio="IoT enthusiast",
    preferences=ProfilePreferences(theme="dark", language="en-US"),
    privacy_settings=ProfilePrivacy(email_visible=False)
)

# Update profile
update_data = ProfileUpdate(
    bio="Senior IoT engineer and maker",
    location="San Francisco, CA"
)

# Update only preferences
pref_update = PreferencesUpdate(
    theme="auto",
    notifications={"email": False, "push": True}
)

# Response with stats
profile_response = ProfileWithStats(
    id="550e8400-e29b-41d4-a716-446655440000",
    name="John Doe",
    username="johndoe",
    created_at=datetime.now(),
    stats=ProfileStats(
        sensors_count=5,
        data_points=12345
    )
)
"""