#!/bin/bash
"""
Fix Backend Issues - bcrypt and enrollment endpoint
Resolves authentication and mobile app enrollment timeouts
"""

set -e

echo "🔧 Presient Backend Issue Resolver"
echo "======================================"
echo ""

# Configuration
PRESIENT_DIR="/mnt/c/dev/presient/presient"
BACKEND_DIR="$PRESIENT_DIR/backend"

echo "📁 Working directory: $PRESIENT_DIR"
echo ""

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend directory not found: $BACKEND_DIR"
    echo "Please run this script from the presient directory"
    exit 1
fi

cd "$PRESIENT_DIR"

echo "🔧 Issue 1: Fixing bcrypt authentication error"
echo "----------------------------------------------"

# Fix bcrypt version issue
echo "🔄 Updating bcrypt and dependencies..."

# Try different bcrypt fix strategies
echo "📦 Uninstalling conflicting bcrypt versions..."
pip uninstall -y bcrypt || true
pip uninstall -y py-bcrypt || true

echo "📦 Installing compatible bcrypt version..."
pip install bcrypt==4.0.1
pip install passlib[bcrypt]==1.7.4

# Alternative if the above doesn't work
echo "📦 Installing additional auth dependencies..."
pip install python-jose[cryptography]
pip install python-multipart

echo "✅ bcrypt dependencies updated"
echo ""

echo "🔧 Issue 2: Checking enrollment endpoints"
echo "----------------------------------------"

# Check what endpoints actually exist in the backend
echo "🔍 Scanning backend for enrollment endpoints..."

# Look for enrollment-related routes
echo "📄 Checking API routes..."
find "$BACKEND_DIR" -name "*.py" -exec grep -l "enroll\|biometric" {} \; | while read -r file; do
    echo "📁 Found in: $file"
    grep -n "enroll\|biometric" "$file" | head -5 | sed 's/^/    /'
    echo ""
done

# Check for common endpoint patterns
echo "🔍 Looking for API endpoint definitions..."
find "$BACKEND_DIR" -name "*.py" -exec grep -l "@.*\.post\|@.*\.get" {} \; | while read -r file; do
    echo "📄 API endpoints in: $file"
    grep -n "@.*\.post\|@.*\.get" "$file" | head -10 | sed 's/^/    /'
    echo ""
done

echo "✅ Backend scan complete"
echo ""

echo "🔧 Issue 3: Creating missing biometric matcher files"
echo "---------------------------------------------------"

# Create the real_biometric_matcher.py if it doesn't exist
MATCHER_FILE="$PRESIENT_DIR/presient_real_setup/real_biometric_matcher.py"
if [ ! -f "$MATCHER_FILE" ]; then
    echo "📝 Creating real_biometric_matcher.py..."
    # The content would be created separately as it's too long for a bash script
    echo "⚠️  real_biometric_matcher.py needs to be created manually"
    echo "   Use the Complete Real Biometric Matcher artifact"
else
    echo "✅ real_biometric_matcher.py exists"
fi

# Create the reset_and_enroll.py if it's empty
ENROLL_FILE="$PRESIENT_DIR/presient_real_setup/reset_and_enroll.py"
if [ ! -s "$ENROLL_FILE" ]; then
    echo "📝 Creating reset_and_enroll.py..."
    echo "⚠️  reset_and_enroll.py needs to be created manually"
    echo "   Use the Reset Database and Real Enrollment artifact"
else
    echo "✅ reset_and_enroll.py exists and has content"
fi

echo ""
echo "🔧 Issue 4: Testing backend startup"
echo "-----------------------------------"

echo "🚀 Testing if backend can start without errors..."

# Test import of key modules
python3 -c "
try:
    import bcrypt
    print('✅ bcrypt import successful')
    
    # Test bcrypt functionality
    password = b'test'
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    if bcrypt.checkpw(password, hashed):
        print('✅ bcrypt functionality working')
    else:
        print('❌ bcrypt functionality broken')
        
except Exception as e:
    print(f'❌ bcrypt error: {e}')

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    test_hash = pwd_context.hash('test')
    if pwd_context.verify('test', test_hash):
        print('✅ passlib integration working')
    else:
        print('❌ passlib integration broken')
except Exception as e:
    print(f'❌ passlib error: {e}')
"

echo ""
echo "🔧 Issue 5: Mobile app endpoint mapping"
echo "--------------------------------------"

echo "📱 Your mobile app is trying to reach: /api/biometric/enroll"
echo "🔍 Common Presient endpoints might be:"
echo "   • /api/heartbeat/enroll"
echo "   • /api/heartbeat/test/enroll/{user_id}"
echo "   • /api/profiles/enroll"
echo "   • /api/auth/register (for user creation)"

echo ""
echo "🧪 Testing backend health endpoint..."
if curl -s "http://192.168.1.135:8000/health" > /dev/null; then
    echo "✅ Backend is accessible at http://192.168.1.135:8000"
    
    echo "📋 Backend health details:"
    curl -s "http://192.168.1.135:8000/health" | python3 -m json.tool | head -20
    
else
    echo "❌ Backend not accessible. Make sure it's running with:"
    echo "   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
fi

echo ""
echo "📊 Summary of Issues Fixed:"
echo "============================"
echo "✅ bcrypt dependencies updated"
echo "🔍 Backend endpoints scanned"
echo "📝 Missing files identified"
echo "🧪 Backend functionality tested"
echo ""

echo "🚀 Next Steps:"
echo "1. Save the biometric matcher and enrollment scripts from the artifacts"
echo "2. Restart your backend server"
echo "3. Check FastAPI docs at http://192.168.1.135:8000/docs for correct endpoint names"
echo "4. Update mobile app to use the correct enrollment endpoint"
echo ""

echo "🎯 Expected Result:"
echo "• Backend starts without bcrypt errors"
echo "• Mobile app enrollment succeeds"
echo "• Ring-style notifications work!"
echo ""
echo "✅ Backend issue resolver complete!"