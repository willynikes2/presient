#!/bin/bash
"""
Fix All Localhost References in Python Scripts
Changes localhost to 192.168.1.135 for proper network access
"""

set -e

echo "🔧 Fixing Localhost References in Python Scripts"
echo "================================================"
echo ""

# Configuration
SETUP_DIR="/mnt/c/dev/presient/presient/presient_real_setup"
OLD_HOST="localhost"
NEW_HOST="192.168.1.135"

echo "📁 Working directory: $SETUP_DIR"
echo "🔄 Changing: $OLD_HOST → $NEW_HOST"
echo ""

# Check if directory exists
if [ ! -d "$SETUP_DIR" ]; then
    echo "❌ Setup directory not found: $SETUP_DIR"
    exit 1
fi

cd "$SETUP_DIR"

echo "🔍 Scanning for localhost references in Python files..."
echo ""

# Function to update localhost in files
update_localhost_in_file() {
    local file="$1"
    
    if [ -f "$file" ]; then
        echo "📄 Checking: $file"
        
        # Check if file contains localhost
        if grep -q "$OLD_HOST" "$file"; then
            echo "  🔍 Found localhost references"
            
            # Create backup
            cp "$file" "${file}.backup"
            echo "  💾 Backup created: ${file}.backup"
            
            # Replace localhost with IP
            sed -i "s/\"$OLD_HOST\"/\"$NEW_HOST\"/g" "$file"
            sed -i "s/'$OLD_HOST'/'$NEW_HOST'/g" "$file"
            
            echo "  ✅ Updated localhost → $NEW_HOST"
            
            # Show changes
            echo "  📝 Changes made:"
            grep -n "$NEW_HOST" "$file" | head -3 | sed 's/^/    /'
            echo ""
        else
            echo "  ✅ No localhost references found"
        fi
    else
        echo "  ⚠️ File not found: $file"
    fi
    echo ""
}

# Update all Python files
echo "🔧 Updating Python files..."
echo ""

# List of files to update
files_to_update=(
    "real_biometric_matcher.py"
    "reset_and_enroll.py"
    "test_real_authentication.py"
    "integrate_real_matching.py"
)

for file in "${files_to_update[@]}"; do
    update_localhost_in_file "$file"
done

# Check for any remaining localhost references
echo "🔍 Checking for any remaining localhost references..."
remaining=$(find . -name "*.py" -exec grep -l "$OLD_HOST" {} \; 2>/dev/null || true)

if [ -n "$remaining" ]; then
    echo "⚠️ Still found localhost in these files:"
    echo "$remaining" | sed 's/^/  /'
    echo ""
    echo "🔍 Manual check needed:"
    echo "$remaining" | while read -r file; do
        if [ -f "$file" ]; then
            echo "📄 $file:"
            grep -n "$OLD_HOST" "$file" | head -3 | sed 's/^/    /'
            echo ""
        fi
    done
else
    echo "✅ No remaining localhost references found!"
fi

echo ""
echo "📊 Summary:"
echo "✅ Updated Python scripts to use $NEW_HOST"
echo "💾 Backups created with .backup extension"
echo "🔄 MQTT connections now point to your backend PC"
echo ""

echo "🧪 Testing MQTT connection to $NEW_HOST..."
if command -v mosquitto_pub >/dev/null 2>&1; then
    if timeout 5 mosquitto_pub -h "$NEW_HOST" -p 1883 -t "test/connection" -m "test" 2>/dev/null; then
        echo "✅ MQTT broker accessible at $NEW_HOST:1883"
    else
        echo "⚠️ MQTT broker test failed. Ensure mosquitto is running on $NEW_HOST"
    fi
else
    echo "💡 Install mosquitto-clients to test MQTT connection"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Run the enrollment: python reset_and_enroll.py"
echo "2. Scripts will now connect to MQTT at $NEW_HOST:1883"
echo "3. Your MR60BHA2 sensor data will be collected properly!"
echo ""
echo "✅ Localhost fix complete!"