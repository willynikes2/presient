#!/bin/bash

echo "🔧 Fixing USER_NOT_FOUND error..."
echo

echo "📝 Step 1: Registering new test user..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}')

echo "Register response: $REGISTER_RESPONSE"
echo

echo "🔑 Step 2: Logging in to get fresh token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}')

echo "Login response: $LOGIN_RESPONSE"
echo

# Extract token using basic tools (works without jq)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token. Check if server is running and registration worked."
    exit 1
fi

echo "✅ Got token: ${TOKEN:0:20}..."
echo

echo "🧪 Step 3: Testing /api/profiles/me endpoint..."
PROFILE_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/profiles/me)

echo "Profile response: $PROFILE_RESPONSE"
echo

if echo "$PROFILE_RESPONSE" | grep -q "USER_NOT_FOUND"; then
    echo "❌ Still getting USER_NOT_FOUND error"
    echo "💡 Try restarting the server: uvicorn backend.main:app --reload"
else
    echo "✅ Success! Profile endpoint is working"
    echo "💾 Saving token to .env for future use..."
    echo "export TOKEN="$TOKEN"" > test_token.sh
    echo "Run 'source test_token.sh' to use this token in your shell"
fi
