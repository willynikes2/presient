#!/usr/bin/env python3
"""
Fix Pydantic v2 config conflicts - remove old Config classes and use model_config
"""

import re
import os

def fix_pydantic_configs(file_path):
    """Fix Pydantic config in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to find classes with both Config and model_config
    # First, find all Pydantic model classes
    class_pattern = r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\):(.*?)(?=class\s+\w+|$)'
    
    def fix_class(match):
        class_name = match.group(1)
        class_body = match.group(2)
        
        # Check if this class has a Config class
        if 'class Config:' in class_body:
            # Extract the Config class content
            config_match = re.search(r'class Config:.*?(?=\n\s{0,4}\w|\n\s*$)', class_body, re.DOTALL)
            if config_match:
                config_content = config_match.group(0)
                
                # Extract config values
                config_dict = {}
                
                # Common config patterns
                if 'orm_mode = True' in config_content or 'from_attributes = True' in config_content:
                    config_dict['from_attributes'] = True
                if 'use_enum_values = True' in config_content:
                    config_dict['use_enum_values'] = True
                if 'validate_assignment = True' in config_content:
                    config_dict['validate_assignment'] = True
                if 'json_encoders' in config_content:
                    # Extract json_encoders
                    encoder_match = re.search(r'json_encoders\s*=\s*({[^}]+})', config_content)
                    if encoder_match:
                        config_dict['json_encoders'] = encoder_match.group(1)
                
                # Remove the Config class
                class_body = class_body.replace(config_content, '')
                
                # Add model_config if we have config values
                if config_dict:
                    # Format the config dict
                    config_str = "model_config = {\n"
                    for key, value in config_dict.items():
                        if isinstance(value, bool):
                            config_str += f'        "{key}": {value},\n'
                        else:
                            config_str += f'        "{key}": {value},\n'
                    config_str = config_str.rstrip(',\n') + '\n    }\n'
                    
                    # Add model_config after class declaration
                    # Find the first line after class declaration
                    lines = class_body.split('\n')
                    insert_index = 1
                    for i, line in enumerate(lines[1:], 1):
                        if line.strip() and not line.strip().startswith('"""'):
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, '    ' + config_str)
                    class_body = '\n'.join(lines)
        
        # Also check if model_config already exists and has conflicts
        if 'model_config = ' in class_body and 'class Config:' not in class_body:
            # Just ensure it's properly formatted
            class_body = re.sub(
                r'model_config\s*=\s*{"from_attributes":\s*True}',
                'model_config = {"from_attributes": True}',
                class_body
            )
        
        return f'class {class_name}({match.group(0).split("(", 1)[1].split(")", 1)[0]}):{class_body}'
    
    # Apply fixes to all classes
    content = re.sub(class_pattern, fix_class, content, flags=re.DOTALL)
    
    # Also fix any standalone model_config issues
    content = re.sub(
        r'model_config = {"from_attributes": True}\s*\n\s*"""',
        'model_config = {"from_attributes": True}\n\n    """',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Fixed {file_path}")
        return True
    return False

def main():
    print("🔧 Fixing Pydantic config conflicts...\n")
    
    files_to_fix = [
        'backend/routes/presence.py',
        'backend/routes/profiles.py',
        'backend/schemas/profiles.py',
        'backend/models/profile.py',
        'backend/models/presence_events.py',
        'backend/models/user.py'
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_pydantic_configs(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n✅ Fixed {fixed_count} files")
    
    # Also do a quick manual fix for the specific error in presence.py
    print("\n📝 Applying specific fix to presence.py...")
    with open('backend/routes/presence.py', 'r') as f:
        content = f.read()
    
    # Remove any duplicate model_config or Config class
    # Fix PresenceEventResponse specifically
    pattern = r'class PresenceEventResponse\(BaseModel\):(.*?)(?=class|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        class_content = match.group(1)
        # Remove any Config class
        class_content = re.sub(r'\s*class Config:.*?(?=\n\s{0,4}\w)', '', class_content, flags=re.DOTALL)
        # Ensure only one model_config
        if class_content.count('model_config') > 1:
            # Keep only the first one
            parts = class_content.split('model_config')
            new_content = parts[0] + 'model_config = {"from_attributes": True}\n' + ''.join(parts[2:])
            class_content = new_content
        elif 'model_config' not in class_content:
            # Add it
            lines = class_content.split('\n')
            lines.insert(1, '    model_config = {"from_attributes": True}')
            class_content = '\n'.join(lines)
        
        content = content[:match.start(1)] + class_content + content[match.end(1):]
    
    with open('backend/routes/presence.py', 'w') as f:
        f.write(content)
    
    print("✓ Applied specific fix to presence.py")

if __name__ == "__main__":
    main()