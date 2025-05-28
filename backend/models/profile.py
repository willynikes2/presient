"""
Enhanced Profile Model with all fields needed for the new routes
Maintains backward compatibility with existing fields
"""

from sqlalchemy import Column, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from backend.db import Base

class Profile(Base):
    __tablename__ = "profiles"
    
    # ==================== Existing Fields ====================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # Keep for backward compatibility
    heartbeat_signature = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ==================== User Association ====================
    # Links profile to auth user
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=True)  # Made nullable for backward compat
    
    # ==================== Basic Profile Info ====================
    username = Column(String(50), unique=True, nullable=True)  # For display
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(100), nullable=True)  # More formal than 'name'
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # ==================== Settings & Preferences ====================
    # Using JSON columns for flexibility
    preferences = Column(JSON, default={}, nullable=False)
    # Example: {"theme": "dark", "language": "en", "timezone": "UTC", "notifications": {...}}
    
    privacy_settings = Column(JSON, default={}, nullable=False)
    # Example: {"profile_visible": true, "email_visible": false, "location_visible": true}
    
    # ==================== Status & Activity ====================
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # ==================== Presence & Location ====================
    # For real-time presence
    online_status = Column(String(20), default="offline", nullable=False)  # online, away, busy, offline
    custom_status_message = Column(String(100), nullable=True)
    
    # For sensor-based presence
    last_known_location = Column(String(100), nullable=True)  # From sensor detection
    last_location_confidence = Column(Float, nullable=True)  # Confidence of last detection
    last_presence_event = Column(DateTime(timezone=True), nullable=True)
    
    # ==================== Metadata ====================
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ==================== Relationships ====================

    # If you have a User model, uncomment this:
    # user = relationship("User", back_populates="profile", uselist=False)
    
    # Relationship to presence events
    presence_events = relationship("PresenceEvent", back_populates="profile", cascade="all, delete-orphan")


    # ==================== Methods ====================
    

    def to_dict(self, include_private=False):
        """Convert profile to dictionary with privacy controls"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "username": self.username,
            "full_name": self.full_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "online_status": self.online_status,
            "custom_status_message": self.custom_status_message
        }
        
        # Apply privacy settings
        privacy = self.privacy_settings or {}
        
        if include_private or privacy.get("email_visible", False):
            data["email"] = self.email
            
        if include_private or privacy.get("location_visible", True):
            data["location"] = self.location
            data["last_known_location"] = self.last_known_location
            
        if include_private:
            data["phone"] = self.phone
            data["preferences"] = self.preferences
            data["privacy_settings"] = self.privacy_settings
            data["last_login"] = self.last_login.isoformat() if self.last_login else None
            
        return data
    
    def update_presence(self, location: str, confidence: float):
        """Update presence information from sensor detection"""
        self.last_known_location = location
        self.last_location_confidence = confidence
        self.last_presence_event = func.now()
        self.last_activity = func.now()
    
    def get_display_name(self):
        """Get the best available display name"""
        return self.full_name or self.username or self.name
    
    def __repr__(self):
        return f"<Profile {self.username or self.name} ({self.id})>"


# ==================== Migration Guide ====================
"""
To migrate your existing database to this new schema, create an Alembic migration:

1. Generate migration:
   alembic revision --autogenerate -m "Enhance profile model"

2. Review and edit the generated migration file to handle existing data:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add new columns with defaults for existing rows
    op.add_column('profiles', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('profiles', sa.Column('username', sa.String(50), nullable=True))
    op.add_column('profiles', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('profiles', sa.Column('full_name', sa.String(100), nullable=True))
    op.add_column('profiles', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('profiles', sa.Column('location', sa.String(100), nullable=True))
    op.add_column('profiles', sa.Column('website', sa.String(255), nullable=True))
    op.add_column('profiles', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('profiles', sa.Column('avatar_url', sa.String(255), nullable=True))
    
    # JSON columns with defaults
    op.add_column('profiles', sa.Column('preferences', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('profiles', sa.Column('privacy_settings', sa.JSON(), nullable=False, server_default='{}'))
    
    # Status columns
    op.add_column('profiles', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('profiles', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('profiles', sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True))
    op.add_column('profiles', sa.Column('online_status', sa.String(20), nullable=False, server_default='offline'))
    op.add_column('profiles', sa.Column('custom_status_message', sa.String(100), nullable=True))
    
    # Presence columns
    op.add_column('profiles', sa.Column('last_known_location', sa.String(100), nullable=True))
    op.add_column('profiles', sa.Column('last_location_confidence', sa.Float(), nullable=True))
    op.add_column('profiles', sa.Column('last_presence_event', sa.DateTime(timezone=True), nullable=True))
    
    # Metadata
    op.add_column('profiles', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    presence_events = relationship("PresenceEvent", foreign_keys="[PresenceEvent.user_id]", primaryjoin="Profile.user_id == PresenceEvent.user_id", viewonly=True)
    
    # Add unique constraints
    op.create_unique_constraint('uq_profiles_user_id', 'profiles', ['user_id'])
    op.create_unique_constraint('uq_profiles_username', 'profiles', ['username'])
    op.create_unique_constraint('uq_profiles_email', 'profiles', ['email'])

def downgrade():
    # Remove constraints
    op.drop_constraint('uq_profiles_email', 'profiles', type_='unique')
    op.drop_constraint('uq_profiles_username', 'profiles', type_='unique')
    op.drop_constraint('uq_profiles_user_id', 'profiles', type_='unique')
    
    # Remove columns
    op.drop_column('profiles', 'updated_at')
    op.drop_column('profiles', 'last_presence_event')
    op.drop_column('profiles', 'last_location_confidence')
    op.drop_column('profiles', 'last_known_location')
    op.drop_column('profiles', 'custom_status_message')
    op.drop_column('profiles', 'online_status')
    op.drop_column('profiles', 'last_activity')
    op.drop_column('profiles', 'last_login')
    op.drop_column('profiles', 'is_active')
    op.drop_column('profiles', 'privacy_settings')
    op.drop_column('profiles', 'preferences')
    op.drop_column('profiles', 'avatar_url')
    op.drop_column('profiles', 'phone')
    op.drop_column('profiles', 'website')
    op.drop_column('profiles', 'location')
    op.drop_column('profiles', 'bio')
    op.drop_column('profiles', 'full_name')
    op.drop_column('profiles', 'email')
    op.drop_column('profiles', 'username')
    op.drop_column('profiles', 'user_id')
```

3. Run migration:
   alembic upgrade head
"""

# ==================== Example Usage ====================
"""
# Create a new profile
profile = Profile(
    name="John Doe",
    username="johndoe",
    email="john@example.com",
    full_name="John Michael Doe",
    bio="IoT enthusiast and maker",
    preferences={
        "theme": "dark",
        "language": "en",
        "timezone": "America/New_York",
        "notifications": {
            "email": True,
            "push": True,
            "sms": False
        }
    },
    privacy_settings={
        "profile_visible": True,
        "email_visible": False,
        "location_visible": True,
        "activity_visible": True
    }
)

# Update presence from sensor
profile.update_presence("Living Room", 0.95)

# Get public view of profile
public_data = profile.to_dict(include_private=False)

# Get full view (for profile owner)
private_data = profile.to_dict(include_private=True)
"""
