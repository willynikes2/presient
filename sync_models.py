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
