#!/bin/bash

echo "🔧 Fixing SQLAlchemy relationship issues..."

# 1. Fix the PresenceEvent model
echo -e "\n📝 Fixing PresenceEvent model relationships..."
cat > fix_presence_events_model.py << 'EOF'
import re

# Read the presence_events.py file
with open('backend/models/presence_events.py', 'r') as f:
    content = f.read()

# Remove the problematic profile relationship if it exists
# The issue is that PresenceEvent has user_id but is trying to create a relationship with Profile
# when it should either not have this relationship or use a proper foreign key

# Remove any existing profile relationship
content = re.sub(r'profile\s*=\s*relationship\([^)]+\).*\n', '', content)

# Make sure the user_id is properly defined as a String (not a ForeignKey to Profile)
# because user_id references User, not Profile
content = re.sub(
    r'user_id\s*=\s*Column\(String.*?\)',
    'user_id = Column(String, nullable=False)',  # Simple string column, not a foreign key
    content
)

# Write back the fixed content
with open('backend/models/presence_events.py', 'w') as f:
    f.write(content)

print("✓ Fixed PresenceEvent model")
EOF

python3 fix_presence_events_model.py
rm fix_presence_events_model.py

# 2. Fix the Profile model
echo -e "\n📝 Fixing Profile model relationships..."
cat > fix_profile_model.py << 'EOF'
import re

# Read the profile.py file
with open('backend/models/profile.py', 'r') as f:
    content = f.read()

# Fix the presence_events relationship
# The relationship should use user_id as the join condition
if 'presence_events' in content:
    # Remove existing relationship
    content = re.sub(r'presence_events\s*=\s*relationship\([^)]+\).*\n', '', content)
    
    # Add the correct relationship after the columns
    # Find the last column definition
    import_section = content.split('class Profile')[0]
    class_section = content.split('class Profile')[1]
    
    # Find where to insert the relationship (after column definitions)
    lines = class_section.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if 'Column(' in line:
            insert_index = i + 1
    
    # Insert the correct relationship
    new_relationship = '    presence_events = relationship("PresenceEvent", foreign_keys="[PresenceEvent.user_id]", primaryjoin="Profile.user_id == PresenceEvent.user_id", viewonly=True)'
    lines.insert(insert_index, new_relationship)
    
    # Reconstruct the content
    content = import_section + 'class Profile' + '\n'.join(lines)

# Make sure UUID is properly imported and used
if 'import uuid' not in content:
    content = 'import uuid\n' + content

# Fix id column to have proper default
content = re.sub(
    r'id\s*=\s*Column\(String,\s*primary_key=True\)',
    'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
    content
)

# Fix user_id column to have proper default
content = re.sub(
    r'user_id\s*=\s*Column\(String[^)]*\)',
    'user_id = Column(String, nullable=False, unique=True)',
    content
)

# Write back the fixed content
with open('backend/models/profile.py', 'w') as f:
    f.write(content)

print("✓ Fixed Profile model")
EOF

python3 fix_profile_model.py
rm fix_profile_model.py

# 3. Create a script to verify the models
echo -e "\n🔍 Creating model verification script..."
cat > verify_models.py << 'EOF'
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
EOF

python3 verify_models.py

# 4. Optionally comment out relationships if they're still causing issues
echo -e "\n📝 Creating relationship removal script (use if needed)..."
cat > remove_relationships.py << 'EOF'
"""
Remove problematic relationships entirely
"""

import re

def remove_all_relationships():
    # Remove from PresenceEvent
    try:
        with open('backend/models/presence_events.py', 'r') as f:
            content = f.read()
        
        # Remove any relationship
        content = re.sub(r'^\s*\w+\s*=\s*relationship\([^)]+\).*$', '', content, flags=re.MULTILINE)
        
        with open('backend/models/presence_events.py', 'w') as f:
            f.write(content)
        print("✓ Removed relationships from PresenceEvent")
    except Exception as e:
        print(f"Error with PresenceEvent: {e}")
    
    # Remove from Profile
    try:
        with open('backend/models/profile.py', 'r') as f:
            content = f.read()
        
        # Comment out presence_events relationship
        content = re.sub(
            r'^(\s*presence_events\s*=\s*relationship\([^)]+\).*)$',
            r'# \1  # Commented out due to foreign key issues',
            content,
            flags=re.MULTILINE
        )
        
        with open('backend/models/profile.py', 'w') as f:
            f.write(content)
        print("✓ Commented out presence_events relationship in Profile")
    except Exception as e:
        print(f"Error with Profile: {e}")

if __name__ == "__main__":
    print("🔧 Removing problematic relationships...")
    remove_all_relationships()
    print("\n✅ Done! Restart your server now.")
EOF

echo -e "\n✅ Fix complete!"
echo -e "\n📋 Summary:"
echo "1. Fixed PresenceEvent model to remove problematic 'profile' relationship"
echo "2. Fixed Profile model's presence_events relationship"
echo "3. Created verification script"
echo -e "\n🎯 Next steps:"
echo "1. If you still see errors, run: python3 remove_relationships.py"
echo "2. Restart your server: Ctrl+C and then: uvicorn backend.main:app --reload"
echo "3. Test again: python test_summary.py"