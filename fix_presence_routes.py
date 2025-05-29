#!/usr/bin/env python3
"""
Check and fix presence route registration
"""

import re

print("🔍 Checking route registration...\n")

# 1. Check main.py for route imports and registration
print("📋 Checking main.py...")
with open('backend/main.py', 'r') as f:
    main_content = f.read()

# Check imports
if 'from backend.routes import' in main_content:
    import_match = re.search(r'from backend\.routes import ([^)]+)', main_content)
    if import_match:
        imported = import_match.group(1)
        print(f"Imported routes: {imported}")
        if 'presence' not in imported:
            print("❌ 'presence' not in imports!")
        else:
            print("✓ 'presence' is imported")

# Check route registration
if 'app.include_router(presence.router)' in main_content:
    print("✓ presence.router is registered")
else:
    print("❌ presence.router NOT registered!")

# 2. Check presence.py router configuration
print("\n📋 Checking presence.py router configuration...")
with open('backend/routes/presence.py', 'r') as f:
    presence_content = f.read()

# Check router creation
router_match = re.search(r'router\s*=\s*APIRouter\((.*?)\)', presence_content, re.DOTALL)
if router_match:
    router_config = router_match.group(1)
    print(f"Router configuration: {router_config.strip()}")
    if '/api/presence' not in router_config:
        print("❌ Router prefix not set to /api/presence")
    else:
        print("✓ Router has correct prefix")

# 3. Fix issues
print("\n🔧 Fixing issues...")

# Fix main.py
needs_save = False

# Ensure presence is imported
if 'presence' not in main_content:
    main_content = re.sub(
        r'from backend\.routes import (.*?)$',
        r'from backend.routes import \1, presence',
        main_content,
        flags=re.MULTILINE
    )
    print("✓ Added presence to imports")
    needs_save = True

# Ensure presence router is registered
if 'app.include_router(presence.router)' not in main_content:
    # Find a good place to add it (after auth router)
    auth_router_pos = main_content.find('app.include_router(auth.router)')
    if auth_router_pos != -1:
        # Find the end of the line
        line_end = main_content.find('\n', auth_router_pos)
        if line_end != -1:
            main_content = (
                main_content[:line_end] + 
                '\napp.include_router(presence.router)' + 
                main_content[line_end:]
            )
            print("✓ Added presence router registration")
            needs_save = True
    else:
        # Add it at the end of routers section
        print("⚠️  Could not find a good place to add presence router")

if needs_save:
    with open('backend/main.py', 'w') as f:
        f.write(main_content)
    print("✓ Saved main.py")

# 4. List all registered routes to verify
print("\n📋 Creating route inspection script...")
inspection_script = '''
import sys
sys.path.append('.')

from backend.main import app

print("\\n🔍 Registered Routes:\\n")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        print(f"{methods:<10} {route.path}")

# Count presence routes
presence_routes = [r for r in app.routes if hasattr(r, 'path') and '/presence' in r.path]
print(f"\\n✓ Found {len(presence_routes)} presence routes")
'''

with open('inspect_routes.py', 'w') as f:
    f.write(inspection_script)

print("\n✓ Created inspect_routes.py")
print("\nRun: python inspect_routes.py")
print("to see all registered routes")

# 5. Also fix the deprecated .dict() call in profiles.py
print("\n🔧 Fixing deprecated .dict() call...")
with open('backend/routes/profiles.py', 'r') as f:
    profiles_content = f.read()

profiles_content = profiles_content.replace('.dict(exclude_unset=True)', '.model_dump(exclude_unset=True)')

with open('backend/routes/profiles.py', 'w') as f:
    f.write(profiles_content)

print("✓ Fixed deprecated .dict() call")

print("\n✅ Fixes complete!")
print("\n🎯 Next steps:")
print("1. Run: python inspect_routes.py")
print("2. Restart your server")
print("3. Run tests again: pytest tests/ -v")