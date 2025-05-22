# backend/scripts/seed_fake_data.py
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.base import Base
from backend.models.profile import Profile

# Connect to the SQLite dev DB
engine = create_engine("sqlite:///./presient.db", echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Create a fake user profile
fake_profile = Profile(
    name="Shawn",
    heartbeat_signature="fake_signature_ABC123",
)

session.add(fake_profile)
session.commit()
print("✅ Fake user profile seeded.")
session.close()
