from backend.db.base import Base

seen = set()
duplicates = []

for name in Base.metadata.tables.keys():
    if name in seen:
        duplicates.append(name)
    else:
        seen.add(name)

if duplicates:
    print(f"⚠️ Duplicate tables found: {duplicates}")
else:
    print("✅ No duplicate tables found.")
