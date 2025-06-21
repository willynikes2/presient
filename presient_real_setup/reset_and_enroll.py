#!/usr/bin/env python3
"""
Presient Multi-User Enrollment Script
Allows enrollment of multiple users for biometric matching WITHOUT clearing existing profiles.
"""

import argparse
import sys
import os

# Add current directory to path so we can import the matcher
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_biometric_matcher import RealBiometricMatcher
from biometric_data_collector import BiometricDataCollector

def enroll_user_flow(matcher: RealBiometricMatcher):
    """Enroll a single user without affecting existing profiles"""
    print("\n📝 Enroll New User")
    user_name = input("Enter full name: ").strip()
    if not user_name:
        print("❌ Name cannot be empty")
        return
        
    user_id = user_name.lower().replace(" ", "_")
    print(f"INFO:👤 User: {user_name} (ID: {user_id})")
    
    # Check if user already exists
    if user_id in matcher.profiles:
        overwrite = input(f"⚠️ User '{user_name}' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Enrollment cancelled")
            return

    collector = BiometricDataCollector()
    samples = collector.collect_enrollment_data(user_name)

    # Check if samples were collected
    if not samples:
        print("❌ No samples collected. Enrollment failed for this user.")
        return

    if len(samples) < 5:
        print(f"❌ Insufficient samples ({len(samples)}). Need at least 5 for enrollment.")
        return

    # Enroll user using the correct method
    try:
        profile = matcher.enroll_user_with_samples(user_id, user_name, samples)
        print(f"✅ Enrollment complete for: {user_name}")
        print(f"💓 Baseline: {profile.heart_rate_baseline:.1f} BPM")
        print(f"📊 Range: {profile.heart_rate_range[0]:.1f} - {profile.heart_rate_range[1]:.1f} BPM")
        print(f"🎯 Confidence threshold: {profile.confidence_threshold:.0%}")
        
    except Exception as e:
        print(f"❌ Enrollment failed: {e}")

def main():
    """Main multi-user enrollment function"""
    parser = argparse.ArgumentParser(description="Presient Multi-User Enrollment Script")
    parser.add_argument("--reset", action="store_true", help="Reset all profiles before enrolling")
    parser.add_argument("--list", action="store_true", help="List existing profiles and exit")
    args = parser.parse_args()

    print("📊 Multi-User Real Biometric Enrollment")
    print("======================================")

    matcher = RealBiometricMatcher()

    # Handle list command
    if args.list:
        if len(matcher.profiles) == 0:
            print("📭 No profiles found in database")
        else:
            print(f"📋 Found {len(matcher.profiles)} existing profiles:")
            for user_id, profile in matcher.profiles.items():
                print(f"  👤 {profile.name} (ID: {profile.user_id})")
                print(f"     💓 Baseline: {profile.heart_rate_baseline:.1f} BPM")
                print(f"     📊 Range: {profile.heart_rate_range[0]:.1f} - {profile.heart_rate_range[1]:.1f} BPM")
                print(f"     🎯 Samples: {profile.samples_count}")
        return

    # Handle reset option
    if args.reset:
        confirm = input("⚠️ This will DELETE ALL existing profiles. Are you sure? (type 'yes'): ").strip()
        if confirm.lower() == 'yes':
            matcher.clear_profiles()
            print("🗑️ All existing profiles cleared.")
        else:
            print("❌ Reset cancelled")
            return
    else:
        print(f"✅ {len(matcher.profiles)} existing profiles loaded.")
        if len(matcher.profiles) > 0:
            print("📋 Existing users:")
            for user_id, profile in matcher.profiles.items():
                print(f"  👤 {profile.name}")

    # Multi-user enrollment loop
    while True:
        enroll_user_flow(matcher)
        again = input("➕ Enroll another user? (y/N): ").strip().lower()
        if again != 'y':
            break

    print(f"\n🏠 Enrollment session complete. Total profiles: {len(matcher.profiles)}")

if __name__ == "__main__":
    main()

