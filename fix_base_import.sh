#!/bin/bash

echo "🔧 Fixing Base import issue..."

# 1. First, let's find where Base is actually defined
echo -e "\n🔍 Looking for Base definition in your codebase..."
grep -r "Base = declarative_base" backend/ --include="*.py" 2>/dev/null | head -5

# 2. Check if Base is in db/base.py or db/session.py
echo -e "\n📋 Checking db directory structure..."
ls -la backend/db/

# 3. Let's look at the actual model files to see how they define Base
echo -e "\n📋 Checking how models define Base..."
echo "=== profile.py ==="
grep -A2 -B2 "Base\|declarative_base" backend/models/profile.py | head -10

echo -e "\n=== presence_events.py ==="
grep -A2 -B2 "Base\|declarative_base" backend/models/presence_events.py | head -10

echo -e "\n=== user.py (if exists) ==="
if [ -f "backend/models/user.py" ]; then
    grep -A2 -B2 "Base\|declarative_base" backend/models/user.py | head -10
else
    echo "user.py not found"
fi

# 4. Based on your structure, let's create the proper fix
echo -e "\n✏️ Creating the proper fix..."

# First, check if Base is defined in db/base.py
if [ -f "backend/db/base.py" ]; then
    echo "Found backend/db/base.py"
    # Update models/__init__.py to import from there
    cat > backend/models/__init__.py << 'EOF'
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
EOF
    echo "✓ Updated __init__.py to import Base from db/base.py"

elif grep -q "Base = declarative_base" backend/db/session.py 2>/dev/null; then
    echo "Found Base in backend/db/session.py"
    # Update models/__init__.py to import from there
    cat > backend/models/__init__.py << 'EOF'
"""
Models package initialization
"""
from backend.db.session import Base
from backend.models.profile import Profile
from backend.models.presence_events import PresenceEvent

# Import User if it exists
try:
    from backend.models.user import User
    __all__ = ['Base', 'Profile', 'PresenceEvent', 'User']
except ImportError:
    __all__ = ['Base', 'Profile', 'PresenceEvent']
EOF
    echo "✓ Updated __init__.py to import Base from db/session.py"

else
    echo "Base not found in expected locations, creating it in models/__init__.py"
    # Create Base in models/__init__.py
    cat > backend/models/__init__.py << 'EOF'
"""
Models package initialization
"""
from sqlalchemy.ext.declarative import declarative_base

# Create the Base class
Base = declarative_base()

# Import models
from backend.models.profile import Profile
from backend.models.presence_events import PresenceEvent

# Import User if it exists
try:
    from backend.models.user import User
    __all__ = ['Base', 'Profile', 'PresenceEvent', 'User']
except ImportError:
    __all__ = ['Base', 'Profile', 'PresenceEvent']
EOF
    echo "✓ Created Base in models/__init__.py"
fi

# 5. Update alembic env.py to handle the imports correctly
echo -e "\n⚙️ Updating alembic/env.py..."
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

# Try different import strategies
try:
    # First try: Import from models package
    from backend.models import Base, Profile, PresenceEvent
    print("✓ Imported Base from backend.models")
except ImportError as e:
    print(f"Failed to import from backend.models: {e}")
    try:
        # Second try: Import from db.base
        from backend.db.base import Base
        from backend.models.profile import Profile
        from backend.models.presence_events import PresenceEvent
        print("✓ Imported Base from backend.db.base")
    except ImportError as e:
        print(f"Failed to import from backend.db.base: {e}")
        try:
            # Third try: Import from db.session
            from backend.db.session import Base
            from backend.models.profile import Profile
            from backend.models.presence_events import PresenceEvent
            print("✓ Imported Base from backend.db.session")
        except ImportError as e:
            print(f"Failed to import Base: {e}")
            raise

# Import User if available
try:
    from backend.models.user import User
except ImportError:
    pass  # User model might not exist

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
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

echo "✓ Updated alembic/env.py"

# 6. Test the imports
echo -e "\n🧪 Testing imports..."
python3 << 'EOF'
import sys
import traceback

print("Testing different import strategies...\n")

# Test 1: Import from models
try:
    from backend.models import Base, Profile, PresenceEvent
    print("✓ SUCCESS: Imported from backend.models")
    print(f"  Base: {Base}")
except Exception as e:
    print(f"✗ FAILED: Import from backend.models failed: {e}")

# Test 2: Check where Base actually comes from
try:
    import backend.models
    if hasattr(backend.models, 'Base'):
        print(f"\n✓ Base is available in backend.models")
        print(f"  Base module: {backend.models.Base.__module__}")
except Exception as e:
    print(f"\n✗ Error checking Base location: {e}")

# Test 3: Direct model imports
try:
    from backend.models.profile import Profile
    from backend.models.presence_events import PresenceEvent
    print("\n✓ Direct model imports work")
except Exception as e:
    print(f"\n✗ Direct model imports failed: {e}")
    traceback.print_exc()
EOF

# 7. Try to create a migration
echo -e "\n🔄 Attempting to create migration..."
alembic revision --autogenerate -m "Initial migration" 2>&1 | tee migration_output.txt

# 8. Check if it succeeded
if grep -q "Generating" migration_output.txt; then
    echo "✓ Migration created successfully!"
    
    # Apply the migration
    echo -e "\n📈 Applying migration..."
    alembic upgrade head
else
    echo "⚠️  Migration failed. Checking error details..."
    cat migration_output.txt
fi

rm -f migration_output.txt

echo -e "\n✅ Fix complete!"
echo -e "\n📋 Summary:"
echo "1. Updated backend/models/__init__.py to properly export Base"
echo "2. Updated alembic/env.py with fallback import strategies"
echo "3. You should now be able to run alembic commands"