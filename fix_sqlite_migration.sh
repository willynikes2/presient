#!/bin/bash

echo "🔧 Fixing SQLite migration issues..."

# 1. First, let's see what migration was created
echo -e "\n📋 Current migration file:"
ls -la alembic/versions/

# 2. Remove the problematic migration
echo -e "\n🗑️ Removing problematic migration..."
rm -f alembic/versions/*_initial_migration.py

# 3. Since SQLite doesn't support ALTER COLUMN, let's stamp the current database as-is
echo -e "\n📈 Stamping current database state..."
# First, clear any existing alembic version
python3 << 'EOF'
import sqlite3
import os

db_path = 'backend/db/dev.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM alembic_version")
        conn.commit()
        print("✓ Cleared alembic_version table")
    except:
        print("✓ No alembic_version entries to clear")
    
    conn.close()
EOF

# 4. Create an empty initial migration (no operations)
echo -e "\n🔄 Creating empty initial migration..."
cat > create_empty_migration.py << 'EOF'
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Create migration file content
migration_content = '''"""Empty initial migration

Revision ID: initial_001
Revises: 
Create Date: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Database already has tables, this is just to establish baseline
    pass


def downgrade() -> None:
    # Nothing to downgrade
    pass
'''

# Write the migration file
import os
os.makedirs('alembic/versions', exist_ok=True)
with open('alembic/versions/initial_001_empty_initial_migration.py', 'w') as f:
    f.write(migration_content)

print("✓ Created empty initial migration")
EOF

python3 create_empty_migration.py
rm create_empty_migration.py

# 5. Apply this empty migration to establish baseline
echo -e "\n📈 Applying empty migration..."
alembic upgrade head

# 6. Now let's check the current database schema
echo -e "\n🔍 Current database schema:"
python3 << 'EOF'
import sqlite3
from tabulate import tabulate

db_path = 'backend/db/dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\nTables in database:")
for table in tables:
    table_name = table[0]
    print(f"\n📊 Table: {table_name}")
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    if columns:
        headers = ['Column', 'Type', 'Not Null', 'Default', 'Primary Key']
        rows = [(col[1], col[2], 'YES' if col[3] else 'NO', col[4], 'YES' if col[5] else 'NO') 
                for col in columns]
        print(tabulate(rows, headers=headers, tablefmt='grid'))

conn.close()
EOF

# 7. Create a proper models synchronization script
echo -e "\n🔧 Creating models sync script..."
cat > sync_models.py << 'EOF'
"""
Sync models with database without using migrations
This is useful for development when the schema is still changing
"""
from backend.db.session import engine
from backend.models import Base, Profile, PresenceEvent
from sqlalchemy import inspect

print("🔍 Checking model-database sync...")

inspector = inspect(engine)
existing_tables = inspector.get_table_names()

print(f"\nExisting tables: {existing_tables}")

# Get model tables
model_tables = Base.metadata.tables.keys()
print(f"Model tables: {list(model_tables)}")

# Check for missing tables
missing_tables = set(model_tables) - set(existing_tables)
if missing_tables:
    print(f"\n⚠️  Missing tables: {missing_tables}")
    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[t] for t in missing_tables])
    print("✓ Created missing tables")
else:
    print("\n✓ All model tables exist")

# For SQLite, we can't easily modify columns, so just report differences
print("\n📋 Schema comparison:")
for table_name in model_tables:
    if table_name in existing_tables:
        print(f"\nTable: {table_name}")
        
        # Get database columns
        db_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        
        # Get model columns
        model_table = Base.metadata.tables[table_name]
        model_columns = {col.name: col for col in model_table.columns}
        
        # Compare
        for col_name, model_col in model_columns.items():
            if col_name in db_columns:
                db_col = db_columns[col_name]
                db_type = str(db_col['type'])
                model_type = str(model_col.type)
                
                # Simple type comparison (not perfect but good enough)
                if db_type.split('(')[0].upper() != model_type.split('(')[0].upper():
                    print(f"  ⚠️  {col_name}: DB has {db_type}, Model has {model_type}")
                else:
                    print(f"  ✓ {col_name}: {model_type}")
            else:
                print(f"  ⚠️  {col_name}: Missing in database (Model has {model_col.type})")
        
        # Check for extra database columns
        for col_name in db_columns:
            if col_name not in model_columns:
                print(f"  ⚠️  {col_name}: Extra column in database")

print("\n✅ Sync check complete!")
print("\nNote: SQLite doesn't support ALTER COLUMN operations.")
print("For major schema changes, you may need to:")
print("1. Backup your data")
print("2. Drop and recreate tables")
print("3. Restore your data")
EOF

# 8. Run the sync check
echo -e "\n🔍 Running sync check..."
python3 sync_models.py

# 9. Create a helper script for future migrations
echo -e "\n📝 Creating migration helper..."
cat > create_migration.sh << 'EOF'
#!/bin/bash
# Helper script to create SQLite-compatible migrations

if [ -z "$1" ]; then
    echo "Usage: ./create_migration.sh <migration_message>"
    exit 1
fi

echo "Creating migration: $1"

# Create the migration
alembic revision -m "$1"

# Find the new migration file
NEW_MIGRATION=$(ls -t alembic/versions/*.py | head -1)

echo "Created migration: $NEW_MIGRATION"
echo ""
echo "⚠️  Remember: SQLite limitations:"
echo "- Cannot ALTER COLUMN"
echo "- Cannot DROP COLUMN (in older versions)"
echo "- Cannot ADD CONSTRAINT"
echo ""
echo "For schema changes in SQLite, you typically need to:"
echo "1. Create new table with new schema"
echo "2. Copy data from old table"
echo "3. Drop old table"
echo "4. Rename new table"
echo ""
echo "Edit your migration file accordingly!"
EOF

chmod +x create_migration.sh

echo -e "\n✅ Fix complete!"
echo -e "\n📋 Summary:"
echo "1. Created empty initial migration to establish baseline"
echo "2. Current database is now tracked by Alembic"
echo "3. Created sync_models.py to check model-database differences"
echo "4. Created create_migration.sh helper for future migrations"
echo -e "\n⚠️  Important notes about SQLite:"
echo "- SQLite has limited ALTER TABLE support"
echo "- For major schema changes, you may need to recreate tables"
echo "- Use the sync_models.py script to check for differences"
echo -e "\n🎯 Your application should now work!"
echo "Restart your FastAPI server: uvicorn backend.main:app --reload"