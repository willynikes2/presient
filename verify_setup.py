import sys
import os

print("🔍 Verifying setup...\n")

# Check database exists
db_locations = ['presient.db', 'backend/db/dev.db']
db_found = False
for db in db_locations:
    if os.path.exists(db):
        print(f"✓ Database found at: {db}")
        db_found = True
        
        # Check tables
        import sqlite3
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"  Tables: {[t[0] for t in tables]}")
        conn.close()
        break

if not db_found:
    print("✗ No database found!")

# Check alembic versions
if os.path.exists('alembic/versions'):
    versions = [f for f in os.listdir('alembic/versions') if f.endswith('.py') and f != '__pycache__']
    print(f"\n✓ Alembic migrations: {len(versions)} found")
    for v in versions:
        print(f"  - {v}")
else:
    print("\n✗ No alembic versions directory!")

# Test imports
try:
    from backend.models import Base
    from backend.models.user import User
    from backend.models.profile import Profile
    from backend.models.presence_events import PresenceEvent
    print("\n✓ All models import successfully")
except Exception as e:
    print(f"\n✗ Model import error: {e}")

print("\n✅ Verification complete!")
