#!/usr/bin/env python3
"""
Perfect score fixes - ensure everything works correctly
"""

import re

print("🎯 Applying perfect score fixes...\n")

# 1. Fix the Profile model to ensure username is always synced
print("1️⃣ Fixing Profile model to sync username...")
with open('backend/models/profile.py', 'r') as f:
    profile_model = f.read()

# Ensure username field is defined
if 'username = Column(String' not in profile_model:
    # Add username field after user_id
    profile_model = re.sub(
        r'(user_id = Column\(String[^)]*\))',
        r'\1\n    username = Column(String, nullable=True, index=True)',
        profile_model
    )
    print("✓ Added username column to Profile model")

with open('backend/models/profile.py', 'w') as f:
    f.write(profile_model)

# 2. Fix the profile creation in routes to always get username from user
print("\n2️⃣ Fixing profile creation to properly get username...")
with open('backend/routes/profiles.py', 'r') as f:
    routes_content = f.read()

# First, let's add a helper to get the actual user data
helper_code = '''
async def get_user_data(user_id: str, db: Session):
    """Get user data from User table"""
    from backend.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    return user
'''

# Add the helper if it doesn't exist
if 'async def get_user_data' not in routes_content:
    # Add after imports
    import_end = routes_content.find('\nrouter = APIRouter')
    if import_end > 0:
        routes_content = routes_content[:import_end] + '\n' + helper_code + routes_content[import_end:]
        print("✓ Added get_user_data helper")

# Now fix the get_my_profile function
pattern = r'(async def get_my_profile.*?)(profile = db\.query\(Profile\).*?if not profile:.*?)(profile = Profile\(.*?\).*?db\.add\(profile\).*?db\.commit\(.*?\))'
match = re.search(pattern, routes_content, re.DOTALL)

if match:
    # Replace the profile creation part
    new_creation = '''# Get the actual user data for username
        user = await get_user_data(current_user["id"], db)
        username = user.username if user else current_user.get("username", current_user["id"][:8])
        
        profile = Profile(
            user_id=current_user["id"],
            username=username,
            email=current_user["email"],
            name=current_user.get("full_name", username),
            full_name=current_user.get("full_name"),
            preferences={},
            privacy_settings=ProfilePrivacy().model_dump()
        )
        db.add(profile)
        db.commit()'''
    
    # Find and replace the profile creation section
    creation_pattern = r'profile = Profile\([^)]+\)[\s\S]*?db\.commit\(\)'
    routes_content = re.sub(creation_pattern, new_creation, routes_content)
    print("✓ Fixed profile creation to include username")

with open('backend/routes/profiles.py', 'w') as f:
    f.write(routes_content)

# 3. Fix the presence status endpoint to work correctly
print("\n3️⃣ Fixing presence status endpoint...")
with open('backend/routes/presence.py', 'r') as f:
    presence_content = f.read()

# Find and update the get_user_presence_status function
status_function = '''@router.get("/status/{user_id}")
async def get_user_presence_status(
    user_id: str,
    include_location: bool = Query(True, description="Include sensor-based location"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> UserPresenceStatus:
    """Get current presence status for a user (online/offline + sensor location)"""
    
    # Try to find profile by different methods
    profile = None
    
    # Method 1: Try by username
    profile = db.query(Profile).filter(Profile.username == user_id).first()
    
    if not profile:
        # Method 2: Try by user_id (foreign key to User)
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    
    if not profile:
        # Method 3: Check if it's a valid UUID and try by profile id
        try:
            import uuid
            uuid_obj = uuid.UUID(user_id)
            profile = db.query(Profile).filter(Profile.id == str(uuid_obj)).first()
        except ValueError:
            pass
    
    if not profile:
        # Try to find the user directly
        from backend.models.user import User
        user = db.query(User).filter(
            (User.username == user_id) | (User.id == user_id)
        ).first()
        
        if user:
            # Create a minimal profile response
            return UserPresenceStatus(
                user_id=user.id,
                status=manager.user_status.get(user.id, {}).get("status", "offline"),
                last_seen=manager.user_status.get(user.id, {}).get("last_seen", datetime.now(timezone.utc)),
                last_activity=manager.last_activity.get(user.id),
                current_location=None,
                confidence=None
            )
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "USER_NOT_FOUND",
                    "user_id": user_id,
                    "message": "User not found"
                }
            )
    
    # Get online/offline status
    status_info = manager.user_status.get(profile.user_id, {
        "status": "offline",
        "last_seen": None
    })
    
    # Get latest sensor-based location if requested
    location = None
    location_confidence = None
    if include_location:
        latest_event = db.query(PresenceEvent)\\
            .filter(PresenceEvent.user_id == profile.user_id)\\
            .order_by(PresenceEvent.timestamp.desc())\\
            .first()
        
        if latest_event:
            # Check if event is recent (within last 5 minutes)
            if (datetime.now(timezone.utc) - latest_event.timestamp).seconds < 300:
                location = manager.sensor_locations.get(profile.user_id)
                location_confidence = latest_event.confidence
    
    return UserPresenceStatus(
        user_id=profile.user_id,
        status=status_info["status"],
        last_seen=status_info.get("last_seen") or datetime.now(timezone.utc),
        last_activity=manager.last_activity.get(profile.user_id),
        current_location=location,
        confidence=location_confidence
    )'''

# Replace the function
function_pattern = r'@router\.get\("/status/\{user_id\}"\)[\s\S]*?(?=@router\.|$)'
presence_content = re.sub(function_pattern, status_function + '\n\n', presence_content)

with open('backend/routes/presence.py', 'w') as f:
    f.write(presence_content)

print("✓ Fixed presence status endpoint")

# 4. Revert the test to expect 200 status
print("\n4️⃣ Reverting test to expect proper 200 status...")
with open('tests/test_integration.py', 'r') as f:
    test_content = f.read()

# Change back to expect 200
test_content = re.sub(
    r'assert response\.status_code in \[200, 404\].*',
    'assert response.status_code == 200',
    test_content
)

# Remove the comment about it being optional
test_content = re.sub(
    r'# This might return 404.*\n',
    '',
    test_content
)

test_content = re.sub(
    r'# 7\. Get user presence status \(optional.*\)',
    '# 7. Get user presence status',
    test_content
)

with open('tests/test_integration.py', 'w') as f:
    f.write(test_content)

print("✓ Reverted test to expect 200 status")

# 5. Create a migration script to update existing profiles
print("\n5️⃣ Creating migration script for existing data...")
migration_script = '''#!/usr/bin/env python3
"""
Migration script to ensure all profiles have usernames
"""
from backend.db.session import SessionLocal
from backend.models.profile import Profile
from backend.models.user import User

def migrate_usernames():
    db = SessionLocal()
    try:
        # Get all profiles without usernames
        profiles = db.query(Profile).filter(
            (Profile.username == None) | (Profile.username == "")
        ).all()
        
        print(f"Found {len(profiles)} profiles without usernames")
        
        for profile in profiles:
            # Get the user
            user = db.query(User).filter(User.id == profile.user_id).first()
            if user:
                profile.username = user.username
                print(f"Updated profile {profile.id} with username {user.username}")
        
        db.commit()
        print("✓ Migration complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_usernames()
'''

with open('migrate_usernames.py', 'w') as f:
    f.write(migration_script)

print("✓ Created migration script")

print("\n✅ All perfect score fixes applied!")
print("\n📋 Summary of changes:")
print("1. Profile model now has username column with index")
print("2. Profile creation properly syncs username from User")
print("3. Presence status endpoint handles all lookup methods")
print("4. Tests expect proper 200 responses")
print("5. Migration script available for existing data")
print("\n🚀 Next steps:")
print("1. Run migration (if you have existing data): python migrate_usernames.py")
print("2. Restart your server")
print("3. Run tests: pytest tests/ -v")
print("\n🎉 All tests should pass with flying colors!")