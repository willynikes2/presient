#!/bin/bash

echo "🔧 Fixing Alembic configuration completely..."

# 1. First, let's find out where your database actually is
echo -e "\n🔍 Finding database location..."
if [ -f "presient.db" ]; then
    echo "✓ Found database at: presient.db"
    DB_PATH="sqlite:///./presient.db"
elif [ -f "backend/db/dev.db" ]; then
    echo "✓ Found database at: backend/db/dev.db"
    DB_PATH="sqlite:///./backend/db/dev.db"
else
    echo "⚠️  No existing database found, will use: presient.db"
    DB_PATH="sqlite:///./presient.db"
fi

# 2. Fix alembic.ini with correct database path
echo -e "\n📝 Updating alembic.ini with correct database path..."
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DB_PATH}|" alembic.ini
echo "✓ Updated database URL to: ${DB_PATH}"

# 3. Clear any existing alembic version from database
echo -e "\n🗄️ Clearing alembic version from database..."
python3 << EOF
import sqlite3
import os

# Try both possible database locations
db_paths = ['presient.db', 'backend/db/dev.db']

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"Found database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if alembic_version table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE alembic_version")
                conn.commit()
                print(f"✓ Dropped alembic_version table from {db_path}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
EOF

# 4. Remove old alembic versions
echo -e "\n🗑️  Removing old migration files..."
rm -rf alembic/versions/*
mkdir -p alembic/versions

# 5. Create proper alembic env.py
echo -e "\n⚙️  Creating proper alembic env.py..."
cat > alembic/env.py << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import your models' Base and all models to ensure they're loaded
from backend.models import Base
from backend.models.user import User
from backend.models.profile import Profile
from backend.models.presence_events import PresenceEvent

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

echo "✓ Created new env.py"

# 6. Ensure all model fixes are applied
echo -e "\n🔧 Ensuring model fixes..."
python3 << 'EOF'
import re

# Fix Profile model
with open('backend/models/profile.py', 'r') as f:
    content = f.read()

# Fix the relationship name
if 'PresenceEvents' in content:
    content = content.replace('PresenceEvents', 'PresenceEvent')
    with open('backend/models/profile.py', 'w') as f:
        f.write(content)
    print("✓ Fixed Profile model relationship")

# Fix main.py imports
with open('backend/main.py', 'r') as f:
    content = f.read()

# Add text import if missing
if 'from sqlalchemy import text' not in content:
    # Find the imports section
    import_line = "from sqlalchemy.orm import Session"
    if import_line in content:
        content = content.replace(import_line, f"{import_line}\nfrom sqlalchemy import text")
    else:
        # Add after first import
        content = content.replace("import os", "import os\nfrom sqlalchemy import text", 1)
    
    with open('backend/main.py', 'w') as f:
        f.write(content)
    print("✓ Added text import to main.py")
EOF

# 7. Create the database tables directly (bypass alembic for now)
echo -e "\n🗄️  Creating database tables..."
python3 << 'EOF'
from backend.db.session import engine
from backend.models import Base

# Import all models to ensure they're registered
from backend.models.user import User
from backend.models.profile import Profile
from backend.models.presence_events import PresenceEvent

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("✓ Database tables created successfully!")

# List all tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nCreated tables: {', '.join(tables)}")
EOF

# 8. Now create the initial migration
echo -e "\n🔄 Creating initial migration..."
alembic revision --autogenerate -m "Initial migration"

# 9. Stamp the database as being at head
echo -e "\n📈 Stamping database with current revision..."
alembic stamp head

# 10. Show current status
echo -e "\n📊 Current Alembic status:"
alembic current

# 11. Create a test script to verify everything works
echo -e "\n🧪 Creating verification script..."
cat > verify_setup.py << 'EOF'
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
EOF

python3 verify_setup.py

echo -e "\n✅ Alembic fix complete!"
echo -e "\n🎯 Next steps:"
echo "1. Restart your FastAPI server: uvicorn backend.main:app --reload"
echo "2. Your database should now be properly initialized"
echo "3. Alembic should work without errors"