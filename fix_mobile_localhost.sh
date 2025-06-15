#!/bin/bash
"""
Fix Mobile App Backend URLs - Replace localhost with PC IP
Changes all localhost references to 192.168.1.135 in mobile app
"""

set -e

# Configuration
MOBILE_DIR="/mnt/c/dev/presient/presient/mobile"
OLD_URL="localhost"
NEW_IP="192.168.1.135"
BACKUP_DIR="mobile_backup_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Presient Mobile App URL Fix"
echo "======================================"
echo "📁 Mobile directory: $MOBILE_DIR"
echo "🔄 Changing: $OLD_URL → $NEW_IP"
echo "💾 Backup directory: $BACKUP_DIR"
echo ""

# Check if mobile directory exists
if [ ! -d "$MOBILE_DIR" ]; then
    echo "❌ Mobile directory not found: $MOBILE_DIR"
    exit 1
fi

cd "$MOBILE_DIR"

# Create backup directory
echo "📦 Creating backup..."
mkdir -p "../$BACKUP_DIR"

# Function to backup file
backup_file() {
    local file="$1"
    local backup_path="../$BACKUP_DIR/$(echo "$file" | sed 's/\//_/g')"
    cp "$file" "$backup_path"
    echo "  💾 Backed up: $file"
}

# Function to replace localhost in file
replace_localhost() {
    local file="$1"
    local temp_file=$(mktemp)
    
    # Check if file contains localhost
    if grep -q "$OLD_URL" "$file"; then
        echo "  🔍 Found localhost in: $file"
        
        # Backup the file
        backup_file "$file"
        
        # Replace different localhost patterns
        sed -E "s|http://$OLD_URL:([0-9]+)|http://$NEW_IP:\1|g" "$file" > "$temp_file"
        sed -i -E "s|https://$OLD_URL:([0-9]+)|https://$NEW_IP:\1|g" "$temp_file"
        sed -i -E "s|$OLD_URL:([0-9]+)|$NEW_IP:\1|g" "$temp_file"
        sed -i -E "s|'$OLD_URL'|'$NEW_IP'|g" "$temp_file"
        sed -i -E "s|\"$OLD_URL\"|\"$NEW_IP\"|g" "$temp_file"
        
        # Move temp file back
        mv "$temp_file" "$file"
        
        echo "  ✅ Updated: $file"
        
        # Show the changes
        echo "  📝 Changes made:"
        grep -n "$NEW_IP" "$file" | head -3 | sed 's/^/    /'
        echo ""
    fi
}

echo "🔍 Scanning for localhost references..."
echo ""

# Find all relevant files (excluding node_modules, .git, etc.)
find . -type f \( \
    -name "*.js" -o \
    -name "*.jsx" -o \
    -name "*.ts" -o \
    -name "*.tsx" -o \
    -name "*.json" -o \
    -name "*.env*" \
\) \
-not -path "./node_modules/*" \
-not -path "./.git/*" \
-not -path "./ios/build/*" \
-not -path "./android/build/*" \
-not -path "./.expo/*" | \
while read -r file; do
    if [ -f "$file" ]; then
        replace_localhost "$file"
    fi
done

echo "🔍 Checking for any remaining localhost references..."
remaining=$(find . -type f \( \
    -name "*.js" -o \
    -name "*.jsx" -o \
    -name "*.ts" -o \
    -name "*.tsx" -o \
    -name "*.json" \
\) \
-not -path "./node_modules/*" \
-not -path "./.git/*" \
-exec grep -l "$OLD_URL" {} \; 2>/dev/null || true)

if [ -n "$remaining" ]; then
    echo "⚠️  Still found localhost in these files:"
    echo "$remaining" | sed 's/^/  /'
    echo ""
    echo "🔍 Manual check needed for these files:"
    echo "$remaining" | while read -r file; do
        if [ -f "$file" ]; then
            echo "📄 $file:"
            grep -n "$OLD_URL" "$file" | head -3 | sed 's/^/    /'
            echo ""
        fi
    done
else
    echo "✅ No remaining localhost references found!"
fi

echo ""
echo "📊 Summary:"
echo "✅ Backup created: ../$BACKUP_DIR"
echo "🔄 Changed: $OLD_URL → $NEW_IP"
echo "📱 Mobile app should now connect to: http://$NEW_IP:8000"
echo ""

# Test if the backend is accessible
echo "🌐 Testing backend connection..."
if curl -s "http://$NEW_IP:8000/health" > /dev/null; then
    echo "✅ Backend is accessible at http://$NEW_IP:8000"
else
    echo "⚠️  Backend not accessible. Make sure it's running with:"
    echo "   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Restart your mobile app development server"
echo "2. Refresh your mobile app"
echo "3. Test the connection and enrollment!"
echo ""
echo "✅ Mobile app URL fix complete!"