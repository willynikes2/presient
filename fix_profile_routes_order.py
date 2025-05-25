#!/usr/bin/env python3
"""Fix the route order in profiles.py so /me routes come before /{profile_id}"""

import re

# Read the file
with open('backend/routes/profiles.py', 'r') as f:
    content = f.read()

# Find all route definitions with their full function blocks
# This regex captures from @router to the next @router or end of file
route_pattern = r'(@router\.[^@]+?)(?=@router|$)'
routes = re.findall(route_pattern, content, re.DOTALL)

# Categorize routes
me_routes = []
id_routes = []
other_routes = []

for route in routes:
    if '"/me"' in route or '"/me/' in route:
        me_routes.append(route)
    elif '"/{profile_id}"' in route:  # Fixed: removed the extra part
        id_routes.append(route)
    else:
        other_routes.append(route)

print(f"Found {len(me_routes)} /me routes")
print(f"Found {len(id_routes)} /{{profile_id}} routes")  # Fixed: escaped the braces
print(f"Found {len(other_routes)} other routes")

# Find where routes start in the file
routes_start = content.find('@router.')
if routes_start == -1:
    print("Could not find routes!")
    exit(1)

# Get everything before routes
before_routes = content[:routes_start]

# Reorder: other routes first, then /me routes, then /{profile_id} routes
new_content = before_routes

# Add routes in correct order
print("\nReordering routes...")
new_content += ''.join(other_routes)
new_content += '\n# ==================== /me routes (must come before /{profile_id}) ====================\n\n'
new_content += ''.join(me_routes)
new_content += '\n# ==================== /{profile_id} routes ====================\n\n'
new_content += ''.join(id_routes)

# Write back
with open('backend/routes/profiles.py', 'w') as f:
    f.write(new_content)

print("✅ Routes reordered successfully!")
print("\nNew route order:")
# Show the new order
new_routes = re.findall(r'@router\.\w+\("([^"]+)"', new_content)
for i, route in enumerate(new_routes, 1):
    print(f"  {i}. {route}")
