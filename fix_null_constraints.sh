#!/bin/bash

echo "🔧 Fixing NULL constraint issues..."

# 1. Fix the Profile model
echo -e "\n📝 Fixing Profile model..."
cat > fix_profile_null_constraints.py << 'EOF'
import re

# Read the profile.py file
with open('backend/models/profile.py', 'r') as f:
    content = f.read()

# Make sure uuid is imported
if 'import uuid' not in content:
    content = 'import uuid\n' + content

# Fix the name field - make it nullable or use full_name as default
content = re.sub(
    r'name\s*=\s*Column\(String[^)]*\)',
    'name = Column(String, nullable=True)',  # Make name nullable
    content
)

# Make sure id has a default
if 'id = Column(String, primary_key=True)' in content:
    content = content.replace(
        'id = Column(String, primary_key=True)',
        'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))'
    )

# Write back
with open('backend/models/profile.py', 'w') as f:
    f.write(content)

print("✓ Fixed Profile model")
EOF

python3 fix_profile_null_constraints.py
rm fix_profile_null_constraints.py

# 2. Fix the PresenceEvent model
echo -e "\n📝 Fixing PresenceEvent model..."
cat > fix_presence_event_null_constraints.py << 'EOF'
import re

# Read the presence_events.py file
with open('backend/models/presence_events.py', 'r') as f:
    content = f.read()

# Make sure uuid is imported
if 'import uuid' not in content:
    content = 'import uuid\n' + content

# Fix the id field to have a default
content = re.sub(
    r'id\s*=\s*Column\(String[^)]*primary_key=True[^)]*\)',
    'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
    content
)

# If id doesn't exist or doesn't have primary_key, add it
if 'id = Column' not in content:
    # Find the class definition
    class_match = re.search(r'class PresenceEvent\(Base\):\s*\n\s*__tablename__.*?\n', content)
    if class_match:
        insert_pos = class_match.end()
        id_line = '\n    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))\n'
        content = content[:insert_pos] + id_line + content[insert_pos:]

# Write back
with open('backend/models/presence_events.py', 'w') as f:
    f.write(content)

print("✓ Fixed PresenceEvent model")
EOF

python3 fix_presence_event_null_constraints.py
rm fix_presence_event_null_constraints.py

# 3. Fix the route that creates profiles
echo -e "\n📝 Fixing profile creation route..."
cat > fix_profile_route.py << 'EOF'
import re

# Read the profiles route file
with open('backend/routes/profiles.py', 'r') as f:
    content = f.read()

# Find the get_my_profile function and fix the profile creation
# The issue is that it's not setting the 'name' field
old_profile_creation = '''profile = Profile(
            user_id=current_user["id"],
            email=current_user["email"],
            full_name=current_user.get("full_name"),
            preferences={},
            privacy_settings=ProfilePrivacy().dict()
        )'''

new_profile_creation = '''profile = Profile(
            user_id=current_user["id"],
            email=current_user["email"],
            name=current_user.get("full_name", current_user.get("username", "User")),  # Use full_name or username for name
            full_name=current_user.get("full_name"),
            preferences={},
            privacy_settings=ProfilePrivacy().dict()
        )'''

content = content.replace(old_profile_creation, new_profile_creation)

# Also fix any .dict() calls to use .model_dump() for Pydantic v2
content = content.replace('.dict()', '.model_dump()')

# Write back
with open('backend/routes/profiles.py', 'w') as f:
    f.write(content)

print("✓ Fixed profile route")
EOF

python3 fix_profile_route.py
rm fix_profile_route.py

# 4. Fix the presence route endpoints
echo -e "\n📝 Fixing presence route endpoints..."
cat > fix_presence_routes.py << 'EOF'
import re

# Read the main.py file to check route registration
with open('backend/main.py', 'r') as f:
    main_content = f.read()

# Make sure presence routes are registered with correct prefix
if 'app.include_router(presence.router)' in main_content:
    # Check if it has the correct prefix
    if 'app.include_router(presence.router, prefix="/api")' not in main_content:
        main_content = main_content.replace(
            'app.include_router(presence.router)',
            'app.include_router(presence.router)'  # The prefix is already in the router
        )
else:
    # Add the router inclusion
    router_section = main_content.find('app.include_router(profiles.router)')
    if router_section != -1:
        insert_pos = main_content.find('\n', router_section)
        main_content = main_content[:insert_pos] + '\napp.include_router(presence.router)' + main_content[insert_pos:]

# Write back
with open('backend/main.py', 'w') as f:
    f.write(main_content)

print("✓ Fixed route registration")
EOF

python3 fix_presence_routes.py
rm fix_presence_routes.py

# 5. Create a database check script
echo -e "\n🔍 Creating database check script..."
cat > check_database.py << 'EOF'
import sqlite3
import os

db_path = 'backend/db/dev.db'
if not os.path.exists(db_path):
    db_path = 'presient.db'

print(f"🔍 Checking database at: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check profiles table schema
print("\n📊 Profiles table schema:")
cursor.execute("PRAGMA table_info(profiles)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL OK'} - Default: {col[4]}")

# Check presence_events table schema
print("\n📊 Presence_events table schema:")
cursor.execute("PRAGMA table_info(presence_events)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL OK'} - Default: {col[4]}")

conn.close()
EOF

python3 check_database.py

# 6. Create migration to fix the database schema
echo -e "\n🔄 Creating migration to fix schema..."
cat > fix_schema.py << 'EOF'
"""
Fix database schema issues
"""
import sqlite3
import os

db_path = 'backend/db/dev.db'
if not os.path.exists(db_path):
    db_path = 'presient.db'

print(f"🔧 Fixing schema in: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Make profiles.name nullable
    print("Making profiles.name nullable...")
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # This is a simplified approach - in production, you'd want to preserve data
    
    # For now, just note what needs to be done
    print("⚠️  Note: profiles.name is NOT NULL - may need to recreate table or provide default values")
    
    # Check if any profiles exist without name
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE name IS NULL")
    null_count = cursor.fetchone()[0]
    if null_count > 0:
        print(f"⚠️  Found {null_count} profiles with NULL name")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()

print("\n✅ Schema check complete")
print("\n📋 Recommendations:")
print("1. The models now have proper defaults for ID fields")
print("2. Profile creation now sets the 'name' field")
print("3. You may need to clear your test database if you have conflicting data")
EOF

python3 fix_schema.py

echo -e "\n✅ Fixes applied!"
echo -e "\n🎯 Next steps:"
echo "1. Restart your server"
echo "2. Run tests again: pytest tests/ -v"
echo "3. If you still have issues, consider clearing the database:"
echo "   - Stop the server"
echo "   - Run: rm backend/db/dev.db"
echo "   - Start the server (it will recreate the database)"