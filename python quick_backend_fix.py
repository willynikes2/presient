#!/usr/bin/env python3
"""
Quick fix for Presient backend import issues
"""

import os
import sys

def fix_backend_init():
    """Fix the problematic backend/__init__.py"""
    init_file = "/mnt/c/dev/presient/presient/backend/__init__.py"
    
    try:
        # Create a minimal __init__.py
        with open(init_file, 'w') as f:
            f.write("# Presient Backend\n")
        
        print(f"✅ Fixed {init_file}")
        
    except Exception as e:
        print(f"❌ Error fixing __init__.py: {e}")

def check_main_py():
    """Check if main.py exists and show its import structure"""
    main_file = "/mnt/c/dev/presient/presient/backend/main.py"
    
    if os.path.exists(main_file):
        print(f"✅ Found {main_file}")
        
        # Show first few lines to check imports
        with open(main_file, 'r') as f:
            lines = f.readlines()[:20]  # First 20 lines
        
        print("📝 First few lines of main.py:")
        for i, line in enumerate(lines, 1):
            if 'import' in line or 'from' in line:
                print(f"{i:2d}: {line.rstrip()}")
    else:
        print(f"❌ {main_file} not found")

def show_directory_structure():
    """Show the directory structure"""
    base_dir = "/mnt/c/dev/presient"
    presient_dir = "/mnt/c/dev/presient/presient"
    backend_dir = "/mnt/c/dev/presient/presient/backend"
    
    print("📁 Directory structure:")
    
    if os.path.exists(base_dir):
        print(f"✅ {base_dir}/")
        if os.path.exists(presient_dir):
            print(f"  ✅ presient/")
            if os.path.exists(backend_dir):
                print(f"    ✅ backend/")
                # List backend contents
                try:
                    items = os.listdir(backend_dir)
                    for item in sorted(items)[:10]:  # Show first 10 items
                        print(f"      📄 {item}")
                except:
                    pass
            else:
                print(f"    ❌ backend/ not found")
        else:
            print(f"  ❌ presient/ not found")
    else:
        print(f"❌ {base_dir} not found")

def main():
    print("🔧 Presient Backend Quick Fix")
    print("=" * 40)
    
    # Show structure
    show_directory_structure()
    print()
    
    # Check main.py
    check_main_py()
    print()
    
    # Fix __init__.py
    fix_backend_init()
    print()
    
    print("🚀 Try these commands:")
    print("1. cd /mnt/c/dev/presient/presient")
    print("2. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("If that fails, try:")
    print("1. cd /mnt/c/dev/presient/presient") 
    print("2. python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()