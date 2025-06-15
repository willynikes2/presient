#!/bin/bash

echo "🎯 Starting Real Biometric Presient System"
echo ""

# Step 1: Check if database needs reset
if [ -f "../backend/db/dev.db" ]; then
    echo "📋 Existing database found"
    echo "Do you want to reset and enroll with real biometric data? (y/n)"
    read -r reset_choice
    
    if [ "$reset_choice" = "y" ]; then
        echo "🗑️ Starting database reset and enrollment..."
        python reset_and_enroll.py
        
        echo ""
        echo "🔄 Please restart your backend server now:"
        echo "   Ctrl+C to stop current server"
        echo "   cd ../presient"
        echo "   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
        echo ""
        echo "Press Enter when backend is restarted..."
        read -r
    fi
else
    echo "⚠️ No database found - please run enrollment first"
    python reset_and_enroll.py
fi

# Step 2: Integrate real matching
echo "🔧 Integrating real biometric matching..."
python integrate_real_matching.py

# Step 3: Test the system
echo ""
echo "🧪 System ready for testing!"
echo ""
echo "Your MR60BHA2 sensor should now:"
echo "✅ Collect real biometric data" 
echo "✅ Match against your enrolled profile"
echo "✅ Send Ring-style notifications on match"
echo ""
echo "Walk near your sensor to test!"

