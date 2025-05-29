#!/usr/bin/env python3
"""
Migration script to ensure all profiles have usernames
"""
from backend.db.session import SessionLocal
from backend.models.profile import Profile
from backend.models.user import User

def migrate_usernames():
    db = SessionLocal()
    try:
        # Get all profiles without usernames
        profiles = db.query(Profile).filter(
            (Profile.username == None) | (Profile.username == "")
        ).all()
        
        print(f"Found {len(profiles)} profiles without usernames")
        
        for profile in profiles:
            # Get the user
            user = db.query(User).filter(User.id == profile.user_id).first()
            if user:
                profile.username = user.username
                print(f"Updated profile {profile.id} with username {user.username}")
        
        db.commit()
        print("✓ Migration complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_usernames()
