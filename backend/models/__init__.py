"""
Models package initialization
"""
from backend.db.base import Base
from backend.models.profile import Profile
from backend.models.presence_events import PresenceEvent

# Import User if it exists
try:
    from backend.models.user import User
    __all__ = ['Base', 'Profile', 'PresenceEvent', 'User']
except ImportError:
    __all__ = ['Base', 'Profile', 'PresenceEvent']
