#!/bin/bash
# Test script for family enrollment and authentication

BASE_URL="https://obscure-dollop-r4xgv6j6wjvgfp7rp-8000.app.github.dev"

echo "🏠 Testing Family Enrollment System"
echo "=================================="

# Step 1: Check initial state (should be empty)
echo ""
echo "📊 Step 1: Checking initial enrolled users..."
curl -s "$BASE_URL/api/biometric/enrolled-users" | jq '.'

# Step 2: Enroll first family member (John)
echo ""
echo "👨 Step 2: Enrolling John Smith..."
curl -s -X POST "$BASE_URL/api/biometric/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john_smith",
    "display_name": "John Smith", 
    "location": "Living Room",
    "heartbeat_pattern": [72, 73, 71, 74, 70, 75, 72, 73, 71, 74, 72, 73, 71, 74, 70, 75, 72, 73, 71, 74, 72, 73, 71, 74, 70, 75, 72, 73, 71, 74],
    "mean_hr": 72.5,
    "std_hr": 1.8,
    "range_hr": 5.0,
    "has_wearable": false,
    "enrollment_duration": 30,
    "device_id": "test_enrollment"
  }' | jq '.'

echo ""
echo "✅ Test complete! Check if John Smith was enrolled successfully."
