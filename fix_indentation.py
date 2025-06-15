#!/usr/bin/env python3
"""
Fix the indentation error in test_integration.py
"""

print("🔧 Fixing indentation error in test_integration.py...\n")

# Read the file
with open('tests/test_integration.py', 'r') as f:
    lines = f.readlines()

# Find the problematic lines around line 75-76
print("📋 Lines around the error (70-80):")
for i in range(69, min(80, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')

print("\n" + "="*60 + "\n")

# Fix the indentation issue
# The problem is that the if statement needs proper indentation
fixed_lines = []
for i, line in enumerate(lines):
    if i == 74 and 'if isinstance(event, str):' in line:
        # Make sure this line has proper indentation (8 spaces for being inside the test function)
        fixed_lines.append('        if isinstance(event, str):\n')
    elif i == 75 and 'event = json.loads(event)' in line:
        # This line needs to be indented under the if (12 spaces)
        fixed_lines.append('            event = json.loads(event)\n')
    else:
        fixed_lines.append(line)

# Write back the fixed content
with open('tests/test_integration.py', 'w') as f:
    f.writelines(fixed_lines)

print("✓ Fixed indentation")

# Show the fixed section
print("\n📋 Fixed lines (70-80):")
for i in range(69, min(80, len(fixed_lines))):
    print(f"{i+1:3d}: {fixed_lines[i]}", end='')

print("\n✅ Indentation fixed!")
print("\n🎯 Now run: pytest tests/ -v")