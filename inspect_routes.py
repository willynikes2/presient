
import sys
sys.path.append('.')

from backend.main import app

print("\n🔍 Registered Routes:\n")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        print(f"{methods:<10} {route.path}")

# Count presence routes
presence_routes = [r for r in app.routes if hasattr(r, 'path') and '/presence' in r.path]
print(f"\n✓ Found {len(presence_routes)} presence routes")
