#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_path = "backend/presient.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("💡 The database might be in a different location or not created yet")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table doesn't exist in database")
            return
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"📊 Found {user_count} users in database")
        
        if user_count == 0:
            print("💡 Database is empty - you need to register a new user")
        else:
            # Show existing users
            cursor.execute("SELECT id, username, email, is_active FROM users LIMIT 10")
            users = cursor.fetchall()
            print("👥 Existing users:")
            for user in users:
                status = "active" if user[3] else "inactive"
                print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]} ({status})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()
