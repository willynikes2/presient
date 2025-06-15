import re

# Read auth.py
with open('backend/routes/auth.py', 'r') as f:
    content = f.read()

# Replace @validator with @field_validator
content = re.sub(r'@validator\(', '@field_validator(', content)

# Add the import
if 'from pydantic import' in content and 'field_validator' not in content:
    content = content.replace(
        'from pydantic import BaseModel, Field, validator',
        'from pydantic import BaseModel, Field, field_validator'
    )

# Write back
with open('backend/routes/auth.py', 'r') as f:
    lines = f.readlines()

# Find the import section and update
for i, line in enumerate(lines):
    if 'from pydantic import' in line and 'validator' in line:
        lines[i] = line.replace('validator', 'field_validator')
        break

# Update validator decorators
for i, line in enumerate(lines):
    if '@validator(' in line:
        lines[i] = line.replace('@validator(', '@field_validator(')

with open('backend/routes/auth.py', 'w') as f:
    f.writelines(lines)

print("Fixed auth.py")
