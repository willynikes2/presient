#!/usr/bin/env python3
"""
Presient Multi-User Enrollment Script
Allows enrollment of multiple users for biometric matching.
"""

import argparse
from real_biometric_matcher import RealBiometricMatcher
from biometric_data_collector import BiometricDataCollector # Corrected import

def enroll_user_flow(matcher: RealBiometricMatcher):
    print("\n📝 Enroll New User")
    user_name = input("Enter full name: ").strip().lower().replace(" ", "_")
    print(f"INFO:👤 User: {user_name}")

    collector = BiometricDataCollector()
    samples = collector.collect_enrollment_data(user_name)

    # --- NEW: Check if samples were collected ---
    if not samples:
        print("❌ No samples collected. Enrollment failed for this user.")
        return

    # --- FIX: Call the correct enrollment method ---
    # The enroll_user_with_samples method takes user_id, name, and samples.
    # We'll use user_name for both user_id and name for simplicity.
    matcher.enroll_user_with_samples(user_name, user_name, samples)
    
    # --- REMOVED: matcher.save_profiles() is no longer needed ---
    # The enroll_user_with_samples method handles saving the profile to the database.

    print(f"✅ Enrollment complete for: {user_name}")

def main():
    parser = argparse.ArgumentParser(description="Presient Multi-User Enrollment Script")
    parser.add_argument("--reset", action="store_true", help="Reset all profiles before enrolling")
    args = parser.parse_args()

    print("📊 Multi-User Real Biometric Enrollment")
    print("======================================")

    matcher = RealBiometricMatcher()

    if args.reset:
        matcher.clear_profiles()
        print("🗑️ All existing profiles cleared.")
    else:
        print(f"✅ {len(matcher.profiles)} existing profiles loaded.")

    while True:
        enroll_user_flow(matcher)
        again = input("➕ Enroll another user? (y/N): ").strip().lower()
        if again != 'y':
            break

    print("\n🏠 Enrollment session complete.")

if __name__ == "__main__":
    main()
