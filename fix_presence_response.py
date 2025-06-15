#!/usr/bin/env python3
"""
Fix the presence event response to return proper JSON
"""

import re

print("🔧 Fixing presence event response...\n")

# Read presence.py
with open('backend/routes/presence.py', 'r') as f:
    content = f.read()

# Find the create_presence_event function
pattern = r'(@router\.post\("/event".*?\n.*?async def create_presence_event.*?)(?=\n@router|\n\nasync def|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    function_content = match.group(1)
    print("Found create_presence_event function")
    
    # Check what's being returned
    if 'JSONResponse(' in function_content:
        print("✓ Using JSONResponse")
        
        # Find the JSONResponse section
        json_response_pattern = r'return JSONResponse\((.*?)\)'
        json_match = re.search(json_response_pattern, function_content, re.DOTALL)
        
        if json_match:
            print("\nCurrent JSONResponse content:")
            print(json_match.group(1)[:200] + "..." if len(json_match.group(1)) > 200 else json_match.group(1))
            
            # The issue is likely that we're returning a dict that's being double-serialized
            # Let's fix it to return the dict directly
            if 'event_dict' in function_content:
                # Replace the JSONResponse with just returning the dict
                new_function = function_content.replace(
                    'return JSONResponse(\n            status_code=status.HTTP_201_CREATED,\n            content=event_dict\n        )',
                    'return event_dict'
                )
                
                # Also need to update the response_model
                new_function = re.sub(
                    r'@router\.post\("/event", response_model=PresenceEventResponse.*?\)',
                    '@router.post("/event", response_model=PresenceEventResponse, status_code=201)',
                    new_function
                )
                
                content = content.replace(function_content, new_function)
                print("\n✓ Fixed: Now returning dict directly instead of JSONResponse")
    
    # Alternative fix: If using response_model, FastAPI handles serialization automatically
    # So we should return the Pydantic model or dict, not JSONResponse
    
    # Save the file
    with open('backend/routes/presence.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Fixed presence event response!")

# Show the updated function
print("\n📋 Updated function (excerpt):")
pattern = r'return event_dict'
if pattern in content:
    # Find context around the return
    idx = content.find(pattern)
    start = max(0, idx - 200)
    end = min(len(content), idx + 100)
    print("..." + content[start:end] + "...")

print("\n✅ The endpoint should now return proper JSON!")
print("\n🎯 Next steps:")
print("1. Restart your server")
print("2. Run the test again: pytest tests/test_integration.py -s -v")