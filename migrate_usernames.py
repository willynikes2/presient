#!/usr/bin/env python3
"""
Migration script to ensure all profiles have usernames
Since users are stored in memory, we'll use the profile's user_id as username
"""
from backend.db.session import SessionLocal
from backend.models.profile import Profile

def migrate_usernames():
    db = SessionLocal()
    try:
        # Get all profiles without usernames
        profiles = db.query(Profile).filter(
            (Profile.username == None) | (Profile.username == "")
        ).all()
        
        print(f"Found {len(profiles)} profiles without usernames")
        
        for profile in profiles:
            # Use user_id as username if no username exists
            # In a real system, you might want to generate a better default
            if not profile.username:
                # Use the first 8 characters of user_id as username
                profile.username = f"user_{profile.user_id[:8]}"
                print(f"Updated profile {profile.id} with username {profile.username}")
        
        db.commit()
        print("✓ Migration complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_usernames()
