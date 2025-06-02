#!/usr/bin/env python3
"""
CLI script to preload test biometric profiles into Presient database

Usage:
    python backend/scripts/load_fake_profiles.py --db presient.db --user_id "user_princeton" --mean 72 --std 3.5 --range 12
    python backend/scripts/load_fake_profiles.py --load-defaults --db presient.db
    python backend/scripts/load_fake_profiles.py --list --db presient.db
"""

import argparse
import sys
import logging
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from utils.biometric_matcher import SQLiteBiometricMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_single_profile(db_path: str, user_id: str, mean_hr: float, std_hr: float, range_hr: float):
    """Load a single biometric profile"""
    try:
        matcher = SQLiteBiometricMatcher(db_path)
        success = matcher.add_profile(user_id, mean_hr, std_hr, range_hr)
        
        if success:
            print(f"✅ Added profile for '{user_id}' - Mean HR: {mean_hr}, Std: {std_hr}, Range: {range_hr}")
            return True
        else:
            print(f"❌ Failed to add profile for '{user_id}'")
            return False
            
    except Exception as e:
        print(f"❌ Error adding profile for '{user_id}': {e}")
        return False

def load_default_profiles(db_path: str):
    """Load a set of default test profiles"""
    default_profiles = [
        {
            "user_id": "user_princeton",
            "mean_hr": 72.0,
            "std_hr": 3.5,
            "range_hr": 12.0,
            "description": "Princeton user - normal resting HR"
        },
        {
            "user_id": "john_doe",
            "mean_hr": 68.0,
            "std_hr": 4.2,
            "range_hr": 15.0,
            "description": "John Doe - slightly lower HR, higher variability"
        },
        {
            "user_id": "jane_smith",
            "mean_hr": 78.0,
            "std_hr": 2.8,
            "range_hr": 10.0,
            "description": "Jane Smith - higher HR, low variability"
        },
        {
            "user_id": "alex_runner",
            "mean_hr": 55.0,
            "std_hr": 6.0,
            "range_hr": 20.0,
            "description": "Alex Runner - athlete with low resting HR"
        },
        {
            "user_id": "senior_user",
            "mean_hr": 85.0,
            "std_hr": 5.5,
            "range_hr": 18.0,
            "description": "Senior user - higher baseline HR"
        }
    ]
    
    print(f"Loading {len(default_profiles)} default test profiles...")
    successful = 0
    
    for profile in default_profiles:
        success = load_single_profile(
            db_path,
            profile["user_id"],
            profile["mean_hr"],
            profile["std_hr"],
            profile["range_hr"]
        )
        if success:
            successful += 1
            print(f"   📝 {profile['description']}")
    
    print(f"\n✅ Successfully loaded {successful}/{len(default_profiles)} profiles")
    return successful

def list_profiles(db_path: str):
    """List all profiles in the database"""
    try:
        matcher = SQLiteBiometricMatcher(db_path)
        profiles = matcher.load_profiles_from_db()
        
        if not profiles:
            print("📭 No biometric profiles found in database")
            return
        
        print(f"📊 Found {len(profiles)} biometric profiles:\n")
        
        for user_id, data in profiles.items():
            print(f"👤 User: {user_id}")
            print(f"   💓 Mean HR: {data['mean_hr']:.1f} bpm")
            print(f"   📈 Std HR: {data['std_hr']:.1f} bpm")
            print(f"   📏 Range HR: {data['range_hr']:.1f} bpm")
            print(f"   📅 Created: {data['created_at']}")
            print()
        
        # Show tolerance info
        print(f"🎯 Matching tolerance: ±{matcher.tolerance_percent}%")
        
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")

def delete_profile(db_path: str, user_id: str):
    """Delete a specific profile"""
    try:
        matcher = SQLiteBiometricMatcher(db_path)
        success = matcher.delete_profile(user_id)
        
        if success:
            print(f"✅ Deleted profile for '{user_id}'")
        else:
            print(f"❌ Profile '{user_id}' not found")
            
    except Exception as e:
        print(f"❌ Error deleting profile '{user_id}': {e}")

def test_matching(db_path: str, test_hr_values: list):
    """Test matching against current profiles"""
    try:
        matcher = SQLiteBiometricMatcher(db_path)
        
        print(f"🧪 Testing biometric matching with HR values: {test_hr_values}")
        
        # Test matching
        matched_user = matcher.match_profile(test_hr_values)
        
        if matched_user:
            print(f"✅ Match found: {matched_user}")
        else:
            print("❌ No match found")
            
        # Show calculation details
        if test_hr_values:
            import statistics
            mean_hr = statistics.mean(test_hr_values)
            std_hr = statistics.stdev(test_hr_values) if len(test_hr_values) > 1 else 0.0
            range_hr = max(test_hr_values) - min(test_hr_values)
            
            print(f"\n📊 Test values calculated:")
            print(f"   💓 Mean HR: {mean_hr:.1f} bpm")
            print(f"   📈 Std HR: {std_hr:.1f} bpm") 
            print(f"   📏 Range HR: {range_hr:.1f} bpm")
        
    except Exception as e:
        print(f"❌ Error testing matching: {e}")

def clear_all_profiles(db_path: str, confirm: bool = False):
    """Clear all profiles from database"""
    if not confirm:
        response = input("⚠️  This will delete ALL biometric profiles. Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
    
    try:
        matcher = SQLiteBiometricMatcher(db_path)
        
        # Get current count
        count = matcher.get_profile_count()
        
        if count == 0:
            print("📭 No profiles to delete")
            return
        
        # Delete all by recreating table
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM biometric_profiles')
        conn.commit()
        conn.close()
        
        print(f"✅ Deleted {count} biometric profiles")
        
    except Exception as e:
        print(f"❌ Error clearing profiles: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Presient Biometric Profile CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single profile
  python backend/scripts/load_fake_profiles.py --db presient.db --user_id "user_princeton" --mean 72 --std 3.5 --range 12
  
  # Load default test profiles
  python backend/scripts/load_fake_profiles.py --load-defaults --db presient.db
  
  # List all profiles
  python backend/scripts/load_fake_profiles.py --list --db presient.db
  
  # Test matching
  python backend/scripts/load_fake_profiles.py --test-match 70 72 75 68 --db presient.db
  
  # Delete profile
  python backend/scripts/load_fake_profiles.py --delete "user_princeton" --db presient.db
        """
    )
    
    parser.add_argument('--db', default='presient.db', help='Database file path (default: presient.db)')
    
    # Single profile options
    parser.add_argument('--user_id', help='User ID for single profile')
    parser.add_argument('--mean', type=float, help='Mean heart rate')
    parser.add_argument('--std', type=float, help='Standard deviation of heart rate')
    parser.add_argument('--range', type=float, help='Heart rate range (max - min)')
    
    # Bulk operations
    parser.add_argument('--load-defaults', action='store_true', help='Load default test profiles')
    parser.add_argument('--list', action='store_true', help='List all profiles')
    parser.add_argument('--clear-all', action='store_true', help='Clear all profiles (with confirmation)')
    
    # Testing
    parser.add_argument('--test-match', nargs='+', type=float, help='Test matching with HR values')
    
    # Profile management
    parser.add_argument('--delete', help='Delete specific user profile')
    
    # Utility
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate database path
    db_path = Path(args.db)
    if not db_path.parent.exists():
        print(f"❌ Database directory does not exist: {db_path.parent}")
        sys.exit(1)
    
    print(f"🗄️  Using database: {args.db}")
    
    # Execute requested action
    if args.user_id and args.mean is not None and args.std is not None and args.range is not None:
        # Add single profile
        load_single_profile(args.db, args.user_id, args.mean, args.std, args.range)
        
    elif args.load_defaults:
        # Load default profiles
        load_default_profiles(args.db)
        
    elif args.list:
        # List profiles
        list_profiles(args.db)
        
    elif args.test_match:
        # Test matching
        test_matching(args.db, args.test_match)
        
    elif args.delete:
        # Delete profile
        delete_profile(args.db, args.delete)
        
    elif args.clear_all:
        # Clear all profiles
        clear_all_profiles(args.db)
        
    else:
        # No action specified, show help
        parser.print_help()
        print("\n💡 Use --load-defaults to quickly add test profiles")

if __name__ == "__main__":
    main()