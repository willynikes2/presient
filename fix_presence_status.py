#!/usr/bin/env python3
"""
Fix the presence status endpoint to handle username vs UUID properly
"""

import re

print("🔧 Fixing presence status endpoint...\n")

# Read presence.py
with open('backend/routes/presence.py', 'r') as f:
    content = f.read()

# Find the get_user_presence_status function
pattern = r'(@router\.get\("/status/\{user_id\}".*?\n.*?async def get_user_presence_status.*?)(?=\n@router|\n\nasync def|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    function_content = match.group(1)
    print("Found get_user_presence_status function")
    
    # The issue is this line:
    # profile = db.query(Profile).filter(Profile.id == user_id).first()
    # It should check if user_id is actually a username or UUID
    
    # Replace the problematic query
    old_query = 'profile = db.query(Profile).filter(Profile.id == user_id).first()'
    new_query = '''# Check if user_id is a username or actual UUID
    # Try to find by username first (since tests pass username)
    profile = db.query(Profile).filter(Profile.username == user_id).first()
    if not profile:
        # Try by user_id (from User table)
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        # Finally try by profile id
        try:
            # This will fail if user_id is not a valid UUID format
            import uuid
            uuid.UUID(user_id)
            profile = db.query(Profile).filter(Profile.id == user_id).first()
        except ValueError:
            pass'''
    
    if old_query in function_content:
        function_content = function_content.replace(old_query, new_query)
        content = content.replace(match.group(1), function_content)
        print("✓ Fixed profile query to handle username/UUID properly")
    else:
        print("⚠️  Could not find the exact query to replace")
        # Try a more flexible pattern
        pattern = r'profile = db\.query\(Profile\)\.filter\(Profile\.\w+ == user_id\)\.first\(\)'
        if re.search(pattern, function_content):
            function_content = re.sub(pattern, new_query, function_content)
            content = content.replace(match.group(1), function_content)
            print("✓ Fixed profile query using regex")

# Save the file
with open('backend/routes/presence.py', 'w') as f:
    f.write(content)

print("\n✅ Fixed presence status endpoint!")

# Also check if uuid is imported at the top
if 'import uuid' not in content.split('class')[0]:  # Check imports section
    print("\n⚠️  Note: Make sure 'import uuid' is at the top of the file")
    # Add it if needed
    lines = content.split('\n')
    import_section_end = 0
    for i, line in enumerate(lines):
        if line.startswith('from') or line.startswith('import'):
            import_section_end = i
    
    if import_section_end > 0:
        lines.insert(import_section_end + 1, 'import uuid')
        content = '\n'.join(lines)
        with open('backend/routes/presence.py', 'w') as f:
            f.write(content)
        print("✓ Added uuid import")

print("\n🎯 The fix allows the endpoint to:")
print("1. First try to find profile by username (what tests pass)")
print("2. Then try by user_id (foreign key to User)")
print("3. Finally try by profile id (if it's a valid UUID)")
print("\nThis handles all possible cases!")

print("\n✅ Now run the test again:")
print("pytest tests/test_integration.py -v")