#!/usr/bin/env python3
"""
Check and fix the specific issue in presence.py
"""

# First, let's look at the problematic section
print("🔍 Checking presence.py around line 45...\n")

with open('backend/routes/presence.py', 'r') as f:
    lines = f.readlines()

# Show lines around line 45
print("Lines 40-55 of presence.py:")
for i in range(max(0, 40), min(len(lines), 56)):
    print(f"{i+1:3d}: {lines[i]}", end='')

print("\n" + "="*60 + "\n")

# Now let's fix it
print("🔧 Fixing PresenceEventResponse class...\n")

with open('backend/routes/presence.py', 'r') as f:
    content = f.read()

# Find the PresenceEventResponse class and everything until the next class or function
import re

# Pattern to find the class and its content
pattern = r'(class PresenceEventResponse\(BaseModel\):.*?)(?=\n(?:class|def|@router)|$)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Found PresenceEventResponse class:")
    print(match.group(1)[:500] + "..." if len(match.group(1)) > 500 else match.group(1))
    print("\n" + "="*60 + "\n")
    
    # Extract the class content
    class_content = match.group(1)
    
    # Check for both Config class and model_config
    has_config_class = 'class Config:' in class_content
    has_model_config = 'model_config' in class_content
    
    print(f"Has Config class: {has_config_class}")
    print(f"Has model_config: {has_model_config}")
    
    if has_config_class and has_model_config:
        print("\n⚠️  Found both Config class and model_config!")
        
        # Remove the Config class
        class_content = re.sub(r'\n\s*class Config:.*?(?=\n\s{0,4}\S|\Z)', '', class_content, flags=re.DOTALL)
        
        # Replace in the original content
        content = content.replace(match.group(1), class_content)
        
        print("✓ Removed Config class, keeping model_config")
    
    elif has_config_class and not has_model_config:
        print("\n⚠️  Found only Config class, converting to model_config...")
        
        # Extract Config content and convert
        config_match = re.search(r'class Config:(.*?)(?=\n\s{0,4}\S|\Z)', class_content, re.DOTALL)
        if config_match:
            config_body = config_match.group(1)
            
            # Build model_config
            model_config_items = []
            if 'orm_mode = True' in config_body:
                model_config_items.append('"from_attributes": True')
            elif 'from_attributes = True' in config_body:
                model_config_items.append('"from_attributes": True')
            
            # Remove Config class
            class_content = re.sub(r'\n\s*class Config:.*?(?=\n\s{0,4}\S|\Z)', '', class_content, flags=re.DOTALL)
            
            # Add model_config after docstring
            lines = class_content.split('\n')
            insert_index = 1
            for i, line in enumerate(lines):
                if i > 0 and line.strip() and not line.strip().startswith('"""'):
                    insert_index = i
                    break
            
            if model_config_items:
                config_line = f'    model_config = {{{", ".join(model_config_items)}}}'
                lines.insert(insert_index, config_line)
            
            class_content = '\n'.join(lines)
            content = content.replace(match.group(1), class_content)
            
            print("✓ Converted Config class to model_config")

# Also check for any other BaseModel classes with the same issue
all_classes = re.findall(r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\):', content)
print(f"\nFound {len(all_classes)} BaseModel classes: {', '.join(all_classes)}")

# Fix each class
for class_name in all_classes:
    pattern = rf'(class {class_name}\(.*?\):.*?)(?=\nclass|\ndef|\n@router|$)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        class_content = match.group(1)
        if 'class Config:' in class_content and 'model_config' in class_content:
            # Remove Config class
            class_content = re.sub(r'\n\s*class Config:.*?(?=\n\s{0,4}\S|\Z)', '', class_content, flags=re.DOTALL)
            content = content.replace(match.group(1), class_content)
            print(f"✓ Fixed {class_name}")

# Write the fixed content
with open('backend/routes/presence.py', 'w') as f:
    f.write(content)

print("\n✅ Fixed presence.py!")

# Show the fixed section
print("\n📋 Fixed PresenceEventResponse class:")
pattern = r'(class PresenceEventResponse\(BaseModel\):.*?)(?=\n(?:class|def|@router)|$)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:300] + "..." if len(match.group(1)) > 300 else match.group(1))