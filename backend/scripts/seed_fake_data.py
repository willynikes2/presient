# backend/scripts/seed_fake_data.py

import os
import sys
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import Base
from ..models.profile import Profile  # Relative import

# Connect to the SQLite dev DB
engine = create_engine("sqlite:///./backend/db/dev.db", echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Create a fake user profile
fake_profile = Profile(
    id="user123",
    name="Shawn",
    heartbeat_hash="fake_hash_ABC123",
    created_at=datetime.datetime.now(),
)

session.add(fake_profile)
session.commit()
print("✅ Fake user profile seeded.")

session.close()
