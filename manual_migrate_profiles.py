from backend.db import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def manual_migrate_profiles():
    """Manually add columns to profiles table"""
    
    with engine.connect() as conn:
        # Get existing columns
        result = conn.execute(text("PRAGMA table_info(profiles)"))
        existing_columns = {row[1] for row in result}
        logger.info(f"Existing columns: {existing_columns}")
        
        # Define columns to add (SQLite syntax)
        columns_to_add = [
            ("username", "VARCHAR(50)"),
            ("email", "VARCHAR(255)"),
            ("full_name", "VARCHAR(100)"),
            ("bio", "TEXT"),
            ("location", "VARCHAR(100)"),
            ("website", "VARCHAR(255)"),
            ("phone", "VARCHAR(20)"),
            ("avatar_url", "VARCHAR(255)"),
            ("preferences", "TEXT DEFAULT '{}'"),
            ("privacy_settings", "TEXT DEFAULT '{}'"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("last_login", "TIMESTAMP"),
            ("last_activity", "TIMESTAMP"),
            ("online_status", "VARCHAR(20) DEFAULT 'offline'"),
            ("custom_status_message", "VARCHAR(100)"),
            ("last_known_location", "VARCHAR(100)"),
            ("last_location_confidence", "FLOAT"),
            ("last_presence_event", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP")
        ]
        
        # Add each column if it doesn't exist
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"Added column {col_name}")
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
            else:
                logger.info(f"Column {col_name} already exists")

if __name__ == "__main__":
    manual_migrate_profiles()
