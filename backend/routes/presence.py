"""
Enhanced Presence Routes - Combines sensor presence detection with user online status
Keeps all existing functionality and adds real-time user presence + SQLite biometric authentication
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
import statistics

from backend.db import get_db
from backend.models.presence_events import PresenceEvent
from backend.models.profile import Profile
from backend.services.mqtt import mqtt_publisher
from backend.routes.auth import get_current_user
import uuid

# Import SQLite biometric matcher
from backend.utils.biometric_matcher import SQLiteBiometricMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/presence", tags=["Presence"])

# Initialize SQLite biometric matcher
biometric_matcher = SQLiteBiometricMatcher()

# ==================== Your Existing Models ====================

class PresenceEventCreate(BaseModel):
    """Schema for creating presence events."""
    user_id: str
    sensor_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    # Add biometric data fields
    heart_rate: Optional[float] = Field(None, ge=30.0, le=220.0)
    breathing_rate: Optional[float] = Field(None, ge=5.0, le=50.0)
    distance: Optional[float] = Field(None, ge=0.0)
    target_count: Optional[int] = Field(1, ge=0)
    
    class Config:
        # TODO: Convert to ConfigDict
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "sensor_id": "sensor001",
                "confidence": 0.95,
                "heart_rate": 72.0,
                "breathing_rate": 16.0,
                "distance": 150.0,
                "target_count": 1
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

# ==================== Your Existing Routes (Enhanced with Biometric Authentication) ====================

@router.post("/event", response_model=PresenceEventResponse, status_code=201)
async def create_presence_event(
    event_data: PresenceEventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new presence detection event with biometric authentication.

    This endpoint receives presence detection data from sensors and:
    1. Performs biometric authentication using heart rate data
    2. Stores the event in the database with authentication result
    3. Publishes the event to MQTT for real-time integrations
    4. Updates user location in connection manager
    5. Returns the created event details with authentication status
    """
    logger.info(f"🎯 Processing presence event from {event_data.sensor_id} - HR: {event_data.heart_rate}")

    try:
        # Initialize authentication variables
        authenticated_user_id = None
        biometric_confidence = 0.0
        authentication_status = "no_biometric_data"
        authentication_message = "No heart rate data provided"

        # Perform biometric authentication if heart rate data is available
        if event_data.heart_rate and 30 <= event_data.heart_rate <= 220:
            logger.info(f"🧬 Performing biometric authentication - HR: {event_data.heart_rate}")
            
            # Create heart rate pattern for matching
            hr_values = [event_data.heart_rate]
            
            # Add variation based on breathing rate if available
            if event_data.breathing_rate and event_data.breathing_rate > 0:
                hr_variation = max(1.0, event_data.breathing_rate * 0.2)
                hr_values.extend([
                    event_data.heart_rate + hr_variation,
                    event_data.heart_rate - hr_variation,
                    event_data.heart_rate + (hr_variation * 0.5)
                ])
            
            # Perform biometric matching
            try:
                matched_user_id = biometric_matcher.match_profile(hr_values)
                
                if matched_user_id:
                    authenticated_user_id = matched_user_id
                    # Calculate confidence based on profile match
                    user_profile = biometric_matcher.get_user_profile(matched_user_id)
                    if user_profile:
                        biometric_confidence = calculate_match_confidence(event_data.heart_rate, user_profile)
                    else:
                        biometric_confidence = 0.8  # Default confidence
                    
                    authentication_status = "authenticated"
                    authentication_message = f"Biometric match: {matched_user_id}"
                    logger.info(f"✅ Biometric authentication successful: {matched_user_id} (confidence: {biometric_confidence:.3f})")
                else:
                    authentication_status = "unknown_person"
                    authentication_message = "No biometric match found - unknown person"
                    logger.info(f"❌ No biometric match found for HR pattern: {hr_values}")
                
            except Exception as e:
                logger.error(f"Biometric matching failed: {e}")
                authentication_status = "matching_error"
                authentication_message = f"Biometric matching error: {str(e)}"
        
        # Use authenticated user ID if available, otherwise use provided user_id
        final_user_id = authenticated_user_id or event_data.user_id

        # Create presence event with authentication results
        presence_event = PresenceEvent(
            user_id=final_user_id,
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
            profile = db.query(Profile).filter(Profile.user_id == final_user_id).first()
            # TODO: Get sensor location from sensor registry
            sensor_location = f"Room-{event_data.sensor_id}"  # Placeholder
        except Exception as e:
            logger.warning(f"Could not fetch profile for user {final_user_id}: {e}")

        # Update user location in connection manager
        if sensor_location:
            manager.update_sensor_location(
                final_user_id,
                sensor_location,
                event_data.confidence
            )

        # Prepare enhanced response with biometric data
        response_data = {
            "event_processed": True,
            "presence_detected": True,
            "event_id": presence_event.id,
            "user_id": final_user_id,
            "sensor_id": event_data.sensor_id,
            "timestamp": presence_event.timestamp.isoformat(),
            "biometric_authentication": {
                "status": authentication_status,
                "authenticated": authenticated_user_id is not None,
                "matched_user_id": authenticated_user_id,
                "confidence": round(biometric_confidence, 3),
                "message": authentication_message
            },
            "sensor_data": {
                "heart_rate": event_data.heart_rate,
                "breathing_rate": event_data.breathing_rate,
                "distance": event_data.distance,
                "target_count": event_data.target_count,
                "sensor_confidence": event_data.confidence
            }
        }

        # Publish to MQTT with enhanced data
        try:
            await mqtt_publisher.publish_presence_event(presence_event, profile)
            
            # Also publish biometric authentication result
            if mqtt_publisher.connected:
                biometric_topic = f"{mqtt_publisher.base_topic}/biometric/authentication"
                biometric_payload = {
                    "event_id": presence_event.id,
                    "sensor_id": event_data.sensor_id,
                    "authentication": response_data["biometric_authentication"],
                    "timestamp": presence_event.timestamp.isoformat()
                }
                await mqtt_publisher.publish(biometric_topic, json.dumps(biometric_payload))
            
            logger.debug(f"Published presence event {presence_event.id} to MQTT")
        except Exception as e:
            logger.error(f"Failed to publish presence event to MQTT: {e}")

        return JSONResponse(
            status_code=201,
            content=response_data
        )

    except Exception as e:
        logger.error(f"Error creating presence event: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create presence event")

# ==================== New Biometric Authentication Endpoints ====================

@router.get("/biometric/enrolled-users")
async def get_biometric_enrolled_users():
    """Get list of users enrolled in biometric system"""
    try:
        profiles = biometric_matcher.load_profiles_from_db()
        
        users = []
        for user_id, profile_data in profiles.items():
            users.append({
                "user_id": user_id,
                "created_at": profile_data.get("created_at"),
                "mean_hr_range": f"{profile_data['mean_hr']:.0f} ± {profile_data['std_hr']:.0f} bpm",
                "hr_range": f"{profile_data['range_hr']:.0f} bpm range"
            })
        
        return {
            "enrolled_users": users,
            "total_count": len(users),
            "matcher_tolerance": f"±{biometric_matcher.tolerance_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get biometric enrolled users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/biometric/enroll")
async def enroll_biometric_user(
    enrollment_data: Dict,
    db: Session = Depends(get_db)
):
    """
    Enroll a new user in the biometric system
    
    Expected data:
    {
        "user_id": "john_doe",
        "heart_rate_samples": [72, 75, 68, 70, 74, 73, 69, 71, 76, 72]
    }
    """
    try:
        user_id = enrollment_data.get("user_id")
        hr_samples = enrollment_data.get("heart_rate_samples", [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        if len(hr_samples) < 5:
            raise HTTPException(status_code=400, detail="At least 5 heart rate samples required for enrollment")
        
        # Validate heart rate samples
        valid_samples = [hr for hr in hr_samples if 30 <= hr <= 220]
        if len(valid_samples) < 5:
            raise HTTPException(status_code=400, detail="Insufficient valid heart rate samples")
        
        # Calculate biometric features
        mean_hr = statistics.mean(valid_samples)
        std_hr = statistics.stdev(valid_samples) if len(valid_samples) > 1 else 0.0
        range_hr = max(valid_samples) - min(valid_samples)
        
        # Add profile to database
        success = biometric_matcher.add_profile(user_id, mean_hr, std_hr, range_hr)
        
        if success:
            logger.info(f"✅ Successfully enrolled user in biometric system: {user_id}")
            return {
                "enrollment_successful": True,
                "user_id": user_id,
                "profile_stats": {
                    "mean_hr": round(mean_hr, 1),
                    "std_hr": round(std_hr, 1),
                    "range_hr": round(range_hr, 1),
                    "sample_count": len(valid_samples)
                },
                "message": f"User {user_id} successfully enrolled in biometric system",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save biometric profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Biometric enrollment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Biometric enrollment failed: {str(e)}")

@router.delete("/biometric/user/{user_id}")
async def delete_biometric_profile(user_id: str):
    """Delete a user's biometric profile"""
    try:
        success = biometric_matcher.delete_profile(user_id)
        
        if success:
            logger.info(f"✅ Deleted biometric profile for user: {user_id}")
            return {
                "deletion_successful": True,
                "user_id": user_id,
                "message": f"Biometric profile for {user_id} deleted successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Biometric profile for {user_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Biometric profile deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/biometric/debug/auth-logs")
async def get_biometric_auth_logs(limit: int = Query(50, ge=1, le=200)):
    """Get recent biometric authentication attempts for debugging"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(biometric_matcher.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, live_mean_hr, live_std_hr, live_range_hr, 
                   matched_user_id, confidence, status
            FROM auth_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            timestamp, live_mean, live_std, live_range, matched_user, confidence, status = row
            logs.append({
                "timestamp": timestamp,
                "live_biometrics": {
                    "mean_hr": round(live_mean, 1) if live_mean else None,
                    "std_hr": round(live_std, 1) if live_std else None,
                    "range_hr": round(live_range, 1) if live_range else None
                },
                "matched_user_id": matched_user,
                "confidence": round(confidence, 3) if confidence else 0.0,
                "status": status
            })
        
        conn.close()
        
        return {
            "biometric_auth_logs": logs,
            "total_entries": len(logs),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get biometric auth logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== New Models for User Status ====================

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
    
    # Try to find profile by different methods
    profile = None
    
    # Method 1: Try by username
    profile = db.query(Profile).filter(Profile.username == user_id).first()
    
    if not profile:
        # Method 2: Try by user_id (foreign key to User)
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    
    if not profile:
        # Method 3: Check if it's a valid UUID and try by profile id
        try:
            import uuid
            uuid_obj = uuid.UUID(user_id)
            profile = db.query(Profile).filter(Profile.id == str(uuid_obj)).first()
        except ValueError:
            pass
    
    if not profile:
        # Try to find the user directly
        # from backend.models.user import User  # Users are in memory, not in DB
        user = None
        
        if user:
            # Create a minimal profile response
            return UserPresenceStatus(
                user_id=user.id,
                status=manager.user_status.get(user.id, {}).get("status", "offline"),
                last_seen=manager.user_status.get(user.id, {}).get("last_seen", datetime.now(timezone.utc)),
                last_activity=manager.last_activity.get(user.id),
                current_location=None,
                confidence=None
            )
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "USER_NOT_FOUND",
                    "user_id": user_id,
                    "message": "User not found"
                }
            )
    
    # Get online/offline status
    status_info = manager.user_status.get(profile.user_id, {
        "status": "offline",
        "last_seen": None
    })
    
    # Get latest sensor-based location if requested
    location = None
    location_confidence = None
    if include_location:
        latest_event = db.query(PresenceEvent)\
            .filter(PresenceEvent.user_id == profile.user_id)\
            .order_by(PresenceEvent.timestamp.desc())\
            .first()
        
        if latest_event:
            # Check if event is recent (within last 5 minutes)
            if (datetime.now(timezone.utc) - latest_event.timestamp).seconds < 300:
                location = manager.sensor_locations.get(profile.user_id)
                location_confidence = latest_event.confidence
    
    return UserPresenceStatus(
        user_id=profile.user_id,
        status=status_info["status"],
        last_seen=status_info.get("last_seen") or datetime.now(timezone.utc),
        last_activity=manager.last_activity.get(profile.user_id),
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

# ==================== Helper Functions ====================

def calculate_match_confidence(current_hr: float, stored_profile: Dict) -> float:
    """Calculate confidence score for a biometric match"""
    if not stored_profile:
        return 0.0
    
    try:
        stored_mean = stored_profile["mean_hr"]
        stored_std = stored_profile["std_hr"]
        
        # Calculate how far current HR is from stored mean in terms of standard deviations
        if stored_std > 0:
            z_score = abs(current_hr - stored_mean) / stored_std
            # Convert z-score to confidence (higher z-score = lower confidence)
            confidence = max(0.0, 1.0 - (z_score * 0.2))
        else:
            # No variability data, use simple percentage difference
            diff_percent = abs(current_hr - stored_mean) / stored_mean * 100
            confidence = max(0.0, 1.0 - (diff_percent / 15.0))  # 15% tolerance
        
        return min(1.0, confidence)
        
    except Exception as e:
        logger.error(f"Confidence calculation failed: {e}")
        return 0.5  # Default moderate confidence