#!/usr/bin/env python3
"""
Fix common issues causing 500 errors
"""

import os
import re

def fix_profile_model():
    """Fix profile model issues"""
    print("Fixing profile model...")
    
    with open("backend/models/profile.py", "r") as f:
        content = f.read()
    
    # Fix imports
    if "import uuid" not in content:
        content = "import uuid\n" + content
    
    # Fix UUID defaults
    content = re.sub(
        r'id = Column\(String, primary_key=True\)',
        'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
        content
    )
    
    # Fix relationship name
    content = content.replace("PresenceEvents", "PresenceEvent")
    
    with open("backend/models/profile.py", "w") as f:
        f.write(content)
    
    print("✓ Fixed profile model")

def fix_presence_model():
    """Fix presence event model issues"""
    print("Fixing presence event model...")
    
    with open("backend/models/presence_events.py", "r") as f:
        content = f.read()
    
    # Fix imports
    if "import uuid" not in content:
        content = "import uuid\n" + content
    
    # Fix UUID defaults
    content = re.sub(
        r'id = Column\(String, primary_key=True\)',
        'id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))',
        content
    )
    
    with open("backend/models/presence_events.py", "w") as f:
        f.write(content)
    
    print("✓ Fixed presence event model")

def fix_route_issues():
    """Fix route registration issues"""
    print("Fixing route issues...")
    
    # Check main.py for proper route inclusion
    with open("backend/main.py", "r") as f:
        content = f.read()
    
    # Ensure presence routes are included
    if "app.include_router(presence.router)" not in content:
        # Find where routers are included
        router_section = content.find("app.include_router(profiles.router)")
        if router_section != -1:
            # Add presence router after profiles router
            content = content[:router_section] + \
                     "app.include_router(profiles.router)\n" + \
                     "app.include_router(presence.router)\n" + \
                     content[router_section + len("app.include_router(profiles.router)"):]
            
            with open("backend/main.py", "w") as f:
                f.write(content)
            print("✓ Added presence router to main.py")
    else:
        print("✓ Presence router already included")

if __name__ == "__main__":
    fix_profile_model()
    fix_presence_model()
    fix_route_issues()
    print("\n✅ Fixes applied! Please restart your server.")
