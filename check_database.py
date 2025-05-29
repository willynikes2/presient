import sqlite3
import os

db_path = 'backend/db/dev.db'
if not os.path.exists(db_path):
    db_path = 'presient.db'

print(f"🔍 Checking database at: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check profiles table schema
print("\n📊 Profiles table schema:")
cursor.execute("PRAGMA table_info(profiles)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL OK'} - Default: {col[4]}")

# Check presence_events table schema
print("\n📊 Presence_events table schema:")
cursor.execute("PRAGMA table_info(presence_events)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL OK'} - Default: {col[4]}")

conn.close()
