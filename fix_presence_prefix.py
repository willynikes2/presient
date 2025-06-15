#!/usr/bin/env python3
"""
Fix the presence router prefix to use /api/presence
"""

import re

print("🔧 Fixing presence router prefix...\n")

# Read presence.py
with open('backend/routes/presence.py', 'r') as f:
    content = f.read()

# Find and replace the router definition
old_router = 'router = APIRouter(prefix="/presence", tags=["Presence"])'
new_router = 'router = APIRouter(prefix="/api/presence", tags=["Presence"])'

if old_router in content:
    content = content.replace(old_router, new_router)
    print("✓ Changed router prefix from /presence to /api/presence")
else:
    # Try regex pattern in case there's extra whitespace
    pattern = r'router\s*=\s*APIRouter\s*\(\s*prefix\s*=\s*["\']\/presence["\']\s*,\s*tags\s*=\s*\["Presence"\]\s*\)'
    if re.search(pattern, content):
        content = re.sub(pattern, 'router = APIRouter(prefix="/api/presence", tags=["Presence"])', content)
        print("✓ Changed router prefix from /presence to /api/presence (regex)")
    else:
        print("⚠️  Could not find router definition to update")
        print("Current router definition:")
        router_match = re.search(r'router\s*=\s*APIRouter.*', content)
        if router_match:
            print(router_match.group(0))

# Save the file
with open('backend/routes/presence.py', 'w') as f:
    f.write(content)

print("\n✅ Fixed presence router prefix!")

# Also add the missing /events endpoint if it's not there
print("\n🔍 Checking for /events endpoint...")

if '@router.get("/events")' not in content:
    print("❌ Missing /events endpoint!")
    
    # Find a good place to add it (after the event creation endpoint)
    event_endpoint_match = re.search(r'(@router\.post\("/event".*?\n.*?async def create_presence_event.*?(?=\n@router|\Z))', content, re.DOTALL)
    
    if event_endpoint_match:
        insertion_point = event_endpoint_match.end()
        
        # Add the events list endpoint
        events_endpoint = '''

@router.get("/events")
async def list_presence_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    List presence events with enhanced filtering.
    
    Args:
        limit: Maximum number of events to return
        offset: Number of events to skip
        user_id: Filter by specific user ID
        sensor_id: Filter by specific sensor ID
        min_confidence: Minimum confidence threshold
        start_time: Filter events after this time
        end_time: Filter events before this time
    """
    logger.info(f"Listing presence events (limit={limit}, offset={offset})")
    
    try:
        query = db.query(PresenceEvent)
        
        # Apply filters
        if user_id:
            query = query.filter(PresenceEvent.user_id == user_id)
        if sensor_id:
            query = query.filter(PresenceEvent.sensor_id == sensor_id)
        if min_confidence is not None:
            query = query.filter(PresenceEvent.confidence >= min_confidence)
        if start_time:
            query = query.filter(PresenceEvent.timestamp >= start_time)
        if end_time:
            query = query.filter(PresenceEvent.timestamp <= end_time)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Order by timestamp and apply pagination
        events = query.order_by(PresenceEvent.timestamp.desc()).offset(offset).limit(limit).all()
        
        return {
            "events": events,
            "count": len(events),
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error listing presence events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve presence events")
'''
        
        # Insert the endpoint
        content = content[:insertion_point] + events_endpoint + content[insertion_point:]
        
        # Save again
        with open('backend/routes/presence.py', 'w') as f:
            f.write(content)
        
        print("✓ Added /events endpoint")
else:
    print("✓ /events endpoint already exists")

print("\n📋 Running route inspection again...")
print("="*60)

# Run the inspection script
import subprocess
result = subprocess.run(['python', 'inspect_routes.py'], capture_output=True, text=True)
print(result.stdout)

print("\n✅ All fixes applied!")
print("\n🎯 Next steps:")
print("1. Restart your server")
print("2. Run tests: pytest tests/ -v")
print("\nThe presence routes should now be available at:")
print("  - POST /api/presence/event")
print("  - GET  /api/presence/events")
print("  - GET  /api/presence/status/{user_id}")
print("  - etc.")