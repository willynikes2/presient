# Fix the relationship in Profile model
import re

# Read the Profile model
with open('backend/models/profile.py', 'r') as f:
    content = f.read()

# Find and comment out or fix the relationship
# Replace the problematic relationship line
content = re.sub(
    r'presence_events = relationship\("PresenceEvent".*?\)',
    'presence_events = relationship("PresenceEvent", back_populates="profile", foreign_keys="PresenceEvent.user_id", primaryjoin="Profile.id == PresenceEvent.user_id")',
    content,
    flags=re.DOTALL
)

# If relationship doesn't exist in the expected format, comment it out
if 'presence_events = relationship' in content and 'primaryjoin=' not in content:
    content = content.replace(
        'presence_events = relationship("PresenceEvent", back_populates="profile", lazy="dynamic")',
        '# presence_events = relationship("PresenceEvent", back_populates="profile", lazy="dynamic")  # TODO: Fix foreign key'
    )

with open('backend/models/profile.py', 'w') as f:
    f.write(content)

print("Fixed Profile model relationship")
