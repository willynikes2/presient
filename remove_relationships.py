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
