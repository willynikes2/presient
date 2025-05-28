"""
Verify that models are properly configured
"""

print("🔍 Verifying model configurations...\n")

# Check PresenceEvent model
print("1️⃣ Checking PresenceEvent model...")
try:
    with open('backend/models/presence_events.py', 'r') as f:
        content = f.read()
    
    issues = []
    if 'profile = relationship' in content:
        issues.append("❌ PresenceEvent still has 'profile' relationship (should be removed)")
    else:
        print("✓ No problematic 'profile' relationship in PresenceEvent")
    
    if 'user_id = Column(String' in content:
        print("✓ user_id is defined as String column")
    else:
        issues.append("❌ user_id not properly defined")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ PresenceEvent model looks good!")
        
except Exception as e:
    print(f"❌ Error checking PresenceEvent: {e}")

# Check Profile model
print("\n2️⃣ Checking Profile model...")
try:
    with open('backend/models/profile.py', 'r') as f:
        content = f.read()
    
    issues = []
    if 'presence_events = relationship' in content:
        if 'primaryjoin=' in content and 'Profile.user_id == PresenceEvent.user_id' in content:
            print("✓ presence_events relationship properly configured")
        else:
            issues.append("❌ presence_events relationship not properly configured")
    else:
        print("⚠️  No presence_events relationship found (optional)")
    
    if 'import uuid' in content:
        print("✓ UUID import found")
    else:
        issues.append("❌ Missing UUID import")
    
    if 'default=lambda: str(uuid.uuid4())' in content or 'default=uuid.uuid4' in content:
        print("✓ UUID default found")
    else:
        print("⚠️  No UUID default found (might be okay)")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ Profile model looks good!")
        
except Exception as e:
    print(f"❌ Error checking Profile: {e}")

# Try to import models
print("\n3️⃣ Testing model imports...")
try:
    from backend.models import Base, Profile, PresenceEvent
    print("✓ All models import successfully")
    
    # Check if models have the expected attributes
    if hasattr(PresenceEvent, 'user_id'):
        print("✓ PresenceEvent has user_id")
    else:
        print("❌ PresenceEvent missing user_id")
    
    if hasattr(Profile, 'user_id'):
        print("✓ Profile has user_id")
    else:
        print("❌ Profile missing user_id")
        
    # Check relationships
    if hasattr(PresenceEvent, 'profile'):
        print("⚠️  PresenceEvent has 'profile' relationship (might cause issues)")
    else:
        print("✓ PresenceEvent doesn't have 'profile' relationship")
        
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Verification complete!")
