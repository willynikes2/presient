"""
Enhanced Presence Routes - Combines sensor presence detection with user online status
Keeps all existing functionality and adds real-time user presence
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Set
from collections import defaultdict
import asyncio
import json

from backend.db import get_db
from backend.models.presence_events import PresenceEvent
from backend.models.profile import Profile
from backend.services.mqtt import mqtt_publisher
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/presence", tags=["Presence"])

# ==================== Your Existing Models ====================

class PresenceEventCreate(BaseModel):
    """Schema for creating presence events."""
    user_id: str
    sensor_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    class Config:
        # TODO: Convert to ConfigDict
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "sensor_id": "sensor001",
                "confidence": 0.95
            }
        }

class PresenceEventResponse(BaseModel):
    """Schema for presence event responses."""
    model_config = {"from_attributes": True}
    
    """Schema for presence event responses."""
    id: str
    user_id: str
    sensor_id: str
    confidence: float
    timestamp: datetime

# ==================== New Models for User Status ====================

class UserPresenceStatus(BaseModel):
    """User online/offline status"""
    user_id: str
    status: str = Field(..., pattern="^(online|away|busy|offline)$")
    last_seen: datetime
    last_activity: Optional[datetime] = None
    current_location: Optional[str] = None  # From sensor detection
    confidence: Optional[float] = None  # From sensor detection

class PresenceStatusUpdate(BaseModel):
    """Update user presence status"""
    status: str = Field(..., pattern="^(online|away|busy|offline)$")
    custom_message: Optional[str] = Field(None, max_length=100)

# ==================== Connection Manager for WebSocket ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.user_status: Dict[str, Dict] = {}
        self.last_activity: Dict[str, datetime] = {}
        self.sensor_locations: Dict[str, str] = {}  # Track user locations from sensors
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id].add(websocket)
        self.user_status[user_id] = {
            "status": "online",
            "last_seen": datetime.now(timezone.utc),
            "connections": len(self.active_connections[user_id])
        }
        await self.broadcast_status_change(user_id, "online")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id].discard(websocket)
        
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
            self.user_status[user_id] = {
                "status": "offline",
                "last_seen": datetime.now(timezone.utc),
                "connections": 0
            }
            asyncio.create_task(self.broadcast_status_change(user_id, "offline"))
    
    async def broadcast_status_change(self, user_id: str, status: str):
        message = {
            "type": "status_change",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Publish to MQTT for system-wide notification
        if mqtt_publisher.connected:
            try:
                await mqtt_publisher.publish_user_status(user_id, status)
            except Exception as e:
                logger.error(f"Failed to publish user status to MQTT: {e}")
        
        # Notify all WebSocket connections
        for uid, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    def update_sensor_location(self, user_id: str, location: str, confidence: float):
        """Update user location based on sensor detection"""
        self.sensor_locations[user_id] = location
        if user_id in self.user_status:
            self.user_status[user_id]["location"] = location
            self.user_status[user_id]["location_confidence"] = confidence

manager = ConnectionManager()

# ==================== Your Existing Routes (Enhanced) ====================

@router.post("/event", response_model=PresenceEventResponse, status_code=201)
async def create_presence_event(
    event_data: PresenceEventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new presence detection event.

    This endpoint receives presence detection data from sensors and:
    1. Stores the event in the database
    2. Publishes the event to MQTT for real-time integrations
    3. Updates user location in connection manager
    4. Returns the created event details
    """
    logger.info(f"Creating presence event for user {event_data.user_id}")

    try:
        # Create presence event
        presence_event = PresenceEvent(
            user_id=event_data.user_id,
            sensor_id=event_data.sensor_id,
            confidence=event_data.confidence,
            timestamp=datetime.now(timezone.utc)
        )

        # Save to database
        db.add(presence_event)
        db.commit()
        db.refresh(presence_event)

        logger.info(f"Presence event {presence_event.id} created successfully")

        # Get profile and sensor location
        profile = None
        sensor_location = None
        try:
            profile = db.query(Profile).filter(Profile.user_id == event_data.user_id).first()
            # TODO: Get sensor location from sensor registry
            sensor_location = f"Room-{event_data.sensor_id}"  # Placeholder
        except Exception as e:
            logger.warning(f"Could not fetch profile for user {event_data.user_id}: {e}")

        # Update user location in connection manager
        if sensor_location:
            manager.update_sensor_location(
                event_data.user_id,
                sensor_location,
                event_data.confidence
            )

        # Publish to MQTT
        try:
            await mqtt_publisher.publish_presence_event(presence_event, profile)
            logger.debug(f"Published presence event {presence_event.id} to MQTT")
        except Exception as e:
            logger.error(f"Failed to publish presence event to MQTT: {e}")

        return JSONResponse(
            status_code=201,
            content=PresenceEventResponse.model_validate(presence_event).model_dump_json()
        )

    except Exception as e:
        logger.error(f"Error creating presence event: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create presence event")


# ==================== New Routes for User Status ====================


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

@router.get("/status/{user_id}")
async def get_user_presence_status(
    user_id: str,
    include_location: bool = Query(True, description="Include sensor-based location"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> UserPresenceStatus:
    """Get current presence status for a user (online/offline + sensor location)"""
    
    # Check if user exists
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "USER_NOT_FOUND",
                "user_id": user_id,
                "message": "User not found"
            }
        )
    
    # Get online/offline status
    status_info = manager.user_status.get(user_id, {
        "status": "offline",
        "last_seen": None
    })
    
    # Get latest sensor-based location if requested
    location = None
    location_confidence = None
    if include_location:
        latest_event = db.query(PresenceEvent)\
            .filter(PresenceEvent.user_id == user_id)\
            .order_by(PresenceEvent.timestamp.desc())\
            .first()
        
        if latest_event:
            # Check if event is recent (within last 5 minutes)
            if (datetime.now(timezone.utc) - latest_event.timestamp).seconds < 300:
                location = manager.sensor_locations.get(user_id)
                location_confidence = latest_event.confidence
    
    return UserPresenceStatus(
        user_id=user_id,
        status=status_info["status"],
        last_seen=status_info.get("last_seen") or datetime.now(timezone.utc),
        last_activity=manager.last_activity.get(user_id),
        current_location=location,
        confidence=location_confidence
    )

@router.get("/status")
async def get_multiple_users_presence(
    user_ids: List[str] = Query(..., description="List of user IDs"),
    include_location: bool = Query(False, description="Include sensor locations"),
    current_user: Dict = Depends(get_current_user)
):
    """Get presence status for multiple users"""
    if len(user_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOO_MANY_USERS",
                "message": "Cannot query more than 100 users at once",
                "limit": 100
            }
        )
    
    results = {}
    for user_id in user_ids:
        status_info = manager.user_status.get(user_id, {
            "status": "offline",
            "last_seen": None
        })
        
        user_status = {
            "status": status_info["status"],
            "last_seen": status_info.get("last_seen").isoformat() if status_info.get("last_seen") else None
        }
        
        if include_location and user_id in manager.sensor_locations:
            user_status["location"] = manager.sensor_locations[user_id]
        
        results[user_id] = user_status
    
    return {
        "users": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.put("/status")
async def update_presence_status(
    update: PresenceStatusUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Manually update user's online status"""
    user_id = current_user["id"]
    
    if user_id not in manager.active_connections:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "NOT_CONNECTED",
                "message": "Must be connected via WebSocket to update status"
            }
        )
    
    # Update status
    manager.user_status[user_id]["status"] = update.status
    if update.custom_message:
        manager.user_status[user_id]["custom_message"] = update.custom_message
    
    # Broadcast change
    await manager.broadcast_status_change(user_id, update.status)
    
    return {
        "status": "success",
        "new_status": update.status,
        "message": "Status updated successfully"
    }

@router.get("/online-users")
async def get_online_users(
    include_away: bool = Query(False, description="Include users with 'away' status"),
    include_locations: bool = Query(False, description="Include sensor-based locations"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get list of currently online users with optional sensor locations"""
    online_users = []
    
    for user_id, status_info in manager.user_status.items():
        if status_info["status"] == "online" or (include_away and status_info["status"] == "away"):
            # Get user profile
            profile = db.query(Profile).filter(Profile.id == user_id).first()
            
            if profile:
                user_info = {
                    "user_id": user_id,
                    "username": profile.username if hasattr(profile, 'username') else profile.name,
                    "status": status_info["status"],
                    "last_activity": manager.last_activity.get(user_id, status_info["last_seen"]).isoformat()
                }
                
                if include_locations and user_id in manager.sensor_locations:
                    user_info["location"] = manager.sensor_locations[user_id]
                    user_info["location_confidence"] = status_info.get("location_confidence")
                
                online_users.append(user_info)
    
    return {
        "online_count": len(online_users),
        "users": online_users,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==================== WebSocket for Real-time Status ====================

@router.websocket("/ws")
async def websocket_presence(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token")
):
    """WebSocket endpoint for real-time presence updates"""
    from jose import JWTError, jwt
    from backend.routes.auth import SECRET_KEY, ALGORITHM
    
    # Validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if not username:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get user from database
        from backend.routes.auth import get_user_by_username
        user = await get_user_by_username(username)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
            
        user_id = user["id"]
        
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return
    except Exception as e:
        await websocket.close(code=4000, reason=f"Authentication failed: {str(e)}")
        return
    
    # Connect
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "status": "online",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        while True:
            # Wait for messages
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                manager.last_activity[user_id] = datetime.now(timezone.utc)
                
            elif data.get("type") == "status_update":
                # Status change
                new_status = data.get("status")
                if new_status in ["online", "away", "busy"]:
                    manager.user_status[user_id]["status"] = new_status
                    await manager.broadcast_status_change(user_id, new_status)
                    
            elif data.get("type") == "activity":
                # Activity update
                manager.last_activity[user_id] = datetime.now(timezone.utc)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)

# ==================== Keep Your Existing Routes ====================

@router.post("/test-mqtt")
async def test_mqtt_publication(current_user: Dict = Depends(get_current_user)):
    """Test endpoint to publish a sample presence event to MQTT."""
    logger.info("Testing MQTT publication")
    
    if not mqtt_publisher.connected:
        raise HTTPException(status_code=503, detail="MQTT not connected")
    
    try:
        # Create a mock presence event
        test_event = PresenceEvent(
            id="test-event-123",
            user_id=current_user["id"],
            sensor_id="test-sensor",
            confidence=0.85,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Publish to MQTT
        await mqtt_publisher.publish_presence_event(test_event, None)
        
        return {
            "success": True,
            "message": "Test presence event published to MQTT",
            "event_id": test_event.id
        }
        
    except Exception as e:
        logger.error(f"Error in MQTT test publication: {e}")
        raise HTTPException(status_code=500, detail=f"MQTT test failed: {str(e)}")

@router.post("/sensors/{sensor_id}/register")
async def register_sensor(
    sensor_id: str,
    location: Optional[str] = None,
    capabilities: Optional[dict] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Register a new sensor with the system."""
    logger.info(f"Registering sensor {sensor_id}")
    
    try:
        sensor_data = {
            "location": location,
            "capabilities": capabilities or {},
            "registration_time": datetime.now(timezone.utc).isoformat(),
            "registered_by": current_user["id"]
        }
        
        # Publish sensor registration to MQTT
        if mqtt_publisher.connected:
            await mqtt_publisher.publish_sensor_registration(sensor_id, sensor_data)
        
        return {
            "success": True,
            "message": f"Sensor {sensor_id} registered successfully",
            "sensor_id": sensor_id,
            "mqtt_published": mqtt_publisher.connected
        }
        
    except Exception as e:
        logger.error(f"Error registering sensor {sensor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to register sensor")

@router.post("/sensors/{sensor_id}/heartbeat")
async def sensor_heartbeat(sensor_id: str):
    """Receive heartbeat/keepalive from a sensor."""
    logger.debug(f"Heartbeat received from sensor {sensor_id}")
    
    try:
        # Publish heartbeat to MQTT
        if mqtt_publisher.connected:
            await mqtt_publisher.publish_heartbeat(sensor_id)
        
        return {
            "success": True,
            "message": "Heartbeat received",
            "sensor_id": sensor_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing heartbeat from sensor {sensor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process heartbeat")

# ==================== Analytics Routes ====================

@router.get("/analytics/user/{user_id}")
async def get_user_presence_analytics(
    user_id: str,
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get presence analytics for a user over a time period"""
    
    # Get all presence events in time range
    events = db.query(PresenceEvent)\
        .filter(PresenceEvent.user_id == user_id)\
        .filter(PresenceEvent.timestamp >= start_date)\
        .filter(PresenceEvent.timestamp <= end_date)\
        .order_by(PresenceEvent.timestamp)\
        .all()
    
    if not events:
        return {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": 0,
            "locations": {},
            "peak_hours": []
        }
    
    # Analyze data
    locations = defaultdict(int)
    hourly_counts = defaultdict(int)
    
    for event in events:
        # Count by sensor/location
        locations[event.sensor_id] += 1
        
        # Count by hour
        hour = event.timestamp.hour
        hourly_counts[hour] += 1
    
    # Find peak hours
    peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "user_id": user_id,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "total_events": len(events),
        "locations": dict(locations),
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "average_confidence": sum(e.confidence for e in events) / len(events)
    }
