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
