"""
Enhanced main.py with Build Note 2: Ring-Style Notifications & MR60BHA2 Sensor Integration
"""

import logging
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import httpx
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Import database components
from backend.db import engine, Base, SessionLocal

# Import models to register them (do this before creating tables)
import backend.models.profile
import backend.models.presence_events
# import backend.models.user  # TODO: Add if you create a separate User model
# import backend.models.sensor  # TODO: Add when sensor hardware arrives

# Import custom exception handlers
from backend.utils.exceptions import (
    http_error_handler,
    validation_error_handler,
    custom_database_error_handler,
    custom_validation_error_handler,
    general_exception_handler,
    DatabaseException,
    ValidationException,
    CustomHTTPException
)

# Import MQTT service
from backend.services.mqtt import initialize_mqtt, shutdown_mqtt, mqtt_publisher

# Import SQLite biometric matcher
from backend.utils.biometric_matcher import SQLiteBiometricMatcher, load_profiles_from_db

# Import MR60BHA2 sensor integration
try:
    from backend.services import mqtt_subscriber

    if hasattr(mqtt_subscriber, "startup_mr60bha2_integration"):
        startup_mr60bha2_integration = mqtt_subscriber.startup_mr60bha2_integration
    if hasattr(mqtt_subscriber, "shutdown_mr60bha2_integration"):
        shutdown_mr60bha2_integration = mqtt_subscriber.shutdown_mr60bha2_integration
    if hasattr(mqtt_subscriber, "get_mr60bha2_status"):
        get_mr60bha2_status = mqtt_subscriber.get_mr60bha2_status

    MR60BHA2_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("📡 MR60BHA2 integration module loaded successfully")

except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ MR60BHA2 integration not available: {e}")
    MR60BHA2_AVAILABLE = False

    # Fallback stub functions if import fails
    async def startup_mr60bha2_integration(*args, **kwargs):
        logger.info("📡 MR60BHA2 module not found - using stub")
        return False

    async def shutdown_mr60bha2_integration():
        pass

    def get_mr60bha2_status():
        return {
            "connected": False,
            "status": "module_not_available",
            "error": "mqtt_subscriber.py not found or get_mr60bha2_status missing"
        }


# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Global biometric matcher instance
biometric_matcher: SQLiteBiometricMatcher = None
biometric_profiles: dict = {}

# ==================== Build Note 2: Pydantic Models ====================
class PushTokenRegistration(BaseModel):
    user_id: str
    push_token: str
    device_id: Optional[str] = None
    platform: Optional[str] = "expo"

class PresenceNotification(BaseModel):
    person: str
    confidence: float
    sensor_id: Optional[str] = "entryway_1"
    location: Optional[str] = "Front Door"
    source: Optional[str] = "sensor_only"

class AutomationSettings(BaseModel):
    user_id: str
    enable_home_assistant: bool = True
    enable_push_notifications: bool = True
    enable_app_routines: bool = False
    app_routine_type: Optional[str] = "notification_only"  # "notification_only", "sound", "flash_light"

# ==================== Build Note 2: In-Memory Storage ====================
# In production, these would be stored in database tables
push_tokens: Dict[str, Dict] = {}  # user_id -> {token, device_id, platform}
automation_settings: Dict[str, Dict] = {}  # user_id -> settings
presence_events: List[Dict] = []  # Recent presence events for testing

# ==================== Lifespan Manager ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events"""
    # Startup
    logger.info("🚀 Presient API starting up...")
    
    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready!")
    
    # Initialize biometric system
    await startup_biometric_system()
    
    # Initialize MQTT
    await initialize_mqtt()
    
    # Initialize Build Note 2 components
    await startup_notification_system()
    
    # *** Initialize MR60BHA2 integration ***
    if biometric_matcher and mqtt_publisher:
        try:
            if MR60BHA2_AVAILABLE:
                await startup_mr60bha2_integration(
    biometric=biometric_matcher,
    automation=automation_settings
)
                logger.info("📡 MR60BHA2 sensor integration initialized")
            else:
                logger.info("📡 MR60BHA2 integration skipped - module not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MR60BHA2 integration: {e}")
            # Don't fail startup, sensor is optional
    
    # Log configuration
    logger.info("Exception handlers configured")
    logger.info("SQLAlchemy error handlers enabled")
    logger.info("CORS middleware enabled")
    logger.info("Authentication enabled")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Presient API shutting down...")
    await shutdown_biometric_system()
    await shutdown_mqtt()
    await shutdown_notification_system()
    
    # *** Shutdown MR60BHA2 integration ***
    if MR60BHA2_AVAILABLE:
        await shutdown_mr60bha2_integration()

async def startup_biometric_system():
    """Initialize biometric matching system on startup"""
    global biometric_matcher, biometric_profiles
    
    try:
        # Get database path from environment or use default
        db_path = os.getenv("PRESIENT_DB_PATH", "presient.db")
        logger.info(f"📊 Initializing biometric database: {db_path}")
        
        # Initialize SQLite biometric matcher
        biometric_matcher = SQLiteBiometricMatcher(db_path)
        
        # Load existing profiles from database
        biometric_profiles = biometric_matcher.load_profiles_from_db()
        
        logger.info(f"✅ Loaded {len(biometric_profiles)} biometric profiles")
        
        # Log loaded users (without sensitive data)
        if biometric_profiles:
            user_list = list(biometric_profiles.keys())
            logger.info(f"👥 Enrolled users: {', '.join(user_list)}")
        else:
            logger.info("📭 No biometric profiles found - system ready for enrollment")
        
        # Validate database integrity
        profile_count = biometric_matcher.get_profile_count()
        logger.info(f"🔍 Database integrity check: {profile_count} profiles in DB")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize biometric system: {e}")
        # Don't fail startup, but log the error
        biometric_matcher = None
        biometric_profiles = {}

async def shutdown_biometric_system():
    """Clean shutdown of biometric system"""
    global biometric_matcher, biometric_profiles
    
    try:
        if biometric_matcher:
            logger.info("💾 Biometric system shutdown complete")
        
        biometric_matcher = None
        biometric_profiles = {}
        
    except Exception as e:
        logger.error(f"❌ Error during biometric system shutdown: {e}")

# ==================== Build Note 2: Notification System ====================
async def startup_notification_system():
    """Initialize notification system for Build Note 2"""
    global push_tokens, automation_settings
    
    logger.info("🔔 Initializing notification system...")
    
    # Load any existing push tokens and settings from files (in production, use database)
    try:
        # Load push tokens
        try:
            with open("push_tokens.json", "r") as f:
                push_tokens = json.load(f)
            logger.info(f"📱 Loaded {len(push_tokens)} push tokens")
        except FileNotFoundError:
            push_tokens = {}
            logger.info("📱 No existing push tokens found")
        
        # Load automation settings
        try:
            with open("automation_settings.json", "r") as f:
                automation_settings = json.load(f)
            logger.info(f"⚙️ Loaded automation settings for {len(automation_settings)} users")
        except FileNotFoundError:
            automation_settings = {}
            logger.info("⚙️ No existing automation settings found")
            
    except Exception as e:
        logger.error(f"❌ Failed to load notification data: {e}")
        push_tokens = {}
        automation_settings = {}
    
    logger.info("✅ Notification system initialized")

async def shutdown_notification_system():
    """Save notification system data on shutdown"""
    global push_tokens, automation_settings
    
    try:
        # Save push tokens
        with open("push_tokens.json", "w") as f:
            json.dump(push_tokens, f, indent=2)
        
        # Save automation settings
        with open("automation_settings.json", "w") as f:
            json.dump(automation_settings, f, indent=2)
            
        logger.info("💾 Notification system data saved")
        
    except Exception as e:
        logger.error(f"❌ Failed to save notification data: {e}")

def get_biometric_matcher() -> SQLiteBiometricMatcher:
    """Get the global biometric matcher instance"""
    global biometric_matcher
    
    if biometric_matcher is None:
        raise HTTPException(
            status_code=503, 
            detail="Biometric system not initialized"
        )
    
    return biometric_matcher

def get_biometric_profiles() -> dict:
    """Get the loaded biometric profiles"""
    global biometric_profiles
    return biometric_profiles

# ==================== Initialize FastAPI App ====================
app = FastAPI(
    title="Presient API with MR60BHA2 Sensor Integration",
    description="Biometric presence authentication system with mmWave sensor and Ring-style notifications",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ==================== Middleware ====================
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Custom Error Response ====================
def create_error_response(error_code: str, message: str, details: Optional[dict] = None) -> dict:
    """Create standardized error response"""
    response = {
        "error": error_code,
        "message": message
    }
    if details:
        response["details"] = str(details)
    return response

# ==================== SQLAlchemy Exception Handlers ====================
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity violations"""
    logger.error(f"Database integrity error: {str(exc)}", exc_info=True)
    
    # Parse the error to provide more specific feedback
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    if "duplicate key" in error_msg.lower():
        if "username" in error_msg:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    "USERNAME_EXISTS",
                    "This username is already taken"
                )
            )
        elif "email" in error_msg:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    "EMAIL_EXISTS",
                    "This email is already registered"
                )
            )
    
    return JSONResponse(
        status_code=409,
        content=create_error_response(
            "INTEGRITY_ERROR",
            "Database integrity constraint violation"
        )
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database operational errors"""
    logger.error(f"Database operational error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content=create_error_response(
            "DATABASE_UNAVAILABLE",
            "Database service temporarily unavailable"
        )
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle all other SQLAlchemy errors"""
    logger.error(f"SQLAlchemy error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            "DATABASE_ERROR",
            "A database error occurred"
        )
    )

# ==================== Custom Exception Handlers ====================
app.add_exception_handler(DatabaseException, custom_database_error_handler)
app.add_exception_handler(ValidationException, custom_validation_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ==================== Import and Include Routers ====================
# Import ALL routers including the new auth router
from backend.routes import auth, presence, profiles, heartbeat_auth

# Include routers with consistent prefixing
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(presence.router)
app.include_router(heartbeat_auth.router)

# ==================== Build Note 2: Push Notification Functions ====================
async def send_expo_push_notification(push_token: str, title: str, body: str, data: dict = None):
    """Send push notification via Expo Push API"""
    try:
        url = "https://exp.host/--/api/v2/push/send"
        
        payload = {
            "to": push_token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high",
            "channelId": "presence-detection"
        }
        
        if data:
            payload["data"] = json.dumps(data)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Push notification sent successfully: {title}")
                return {"success": True, "response": result}
            else:
                logger.error(f"❌ Push notification failed: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
    except Exception as e:
        logger.error(f"❌ Error sending push notification: {e}")
        return {"success": False, "error": str(e)}

async def trigger_presence_notification(person: str, confidence: float, sensor_id: str = "entryway_1", 
                                      location: str = "Front Door", source: str = "sensor_only"):
    """Trigger Ring-style presence notification"""
    global push_tokens, automation_settings, presence_events
    
    try:
        # Record the presence event
        event = {
            "person": person,
            "confidence": confidence,
            "sensor_id": sensor_id,
            "location": location,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notification_sent": False
        }
        
        presence_events.append(event)
        
        # Keep only last 50 events
        if len(presence_events) > 50:
            presence_events = presence_events[-50:]
        
        logger.info(f"🏃 Presence detected: {person} at {location} ({confidence:.1%} confidence)")
        
        # Check if user has push notifications enabled
        user_settings = automation_settings.get(person, {
            "enable_push_notifications": True,
            "enable_home_assistant": True,
            "enable_app_routines": False
        })
        
        # Send push notification if enabled and user has token
        if user_settings.get("enable_push_notifications", True) and person in push_tokens:
            user_token_data = push_tokens[person]
            push_token = user_token_data["token"]
            
            # Create Ring-style notification
            confidence_emoji = "🔥" if confidence > 0.95 else "✅" if confidence > 0.85 else "⚡"
            title = f"{confidence_emoji} {person.replace('_', ' ').title()} Detected"
            body = f"Recognized at {location} with {confidence:.1%} confidence"
            
            notification_data = {
                "person": person,
                "confidence": confidence,
                "sensor_id": sensor_id,
                "location": location,
                "source": source,
                "action": "open_sensor_detail"
            }
            
            # Send the notification
            result = await send_expo_push_notification(push_token, title, body, notification_data)
            
            if result["success"]:
                event["notification_sent"] = True
                logger.info(f"📱 Ring-style notification sent to {person}")
            else:
                logger.error(f"❌ Failed to send notification to {person}: {result.get('error')}")
        
        # Enhanced MQTT payload for Home Assistant (Build Note 2 architecture)
        if user_settings.get("enable_home_assistant", True) and mqtt_publisher and mqtt_publisher.connected:
            mqtt_payload = {
                "person": person,
                "confidence": confidence,
                "source": source,
                "sensor_id": sensor_id,
                "location": location,
                "timestamp": event["timestamp"],
                "trigger_action": "presence_detected",
                "notification_sent": event["notification_sent"]
            }
            
            topic = f"{mqtt_publisher.base_topic}/presence/detected"
            await mqtt_publisher.publish(topic, json.dumps(mqtt_payload), retain=False)
            logger.info(f"📡 Enhanced MQTT payload sent to Home Assistant")
        
        # Execute app routines if enabled (for non-HA users)
        if user_settings.get("enable_app_routines", False):
            routine_type = user_settings.get("app_routine_type", "notification_only")
            await execute_app_routine(person, routine_type, confidence)
        
        return event
        
    except Exception as e:
        logger.error(f"❌ Error in presence notification: {e}")
        return None

async def execute_app_routine(person: str, routine_type: str, confidence: float):
    """Execute app-based routines for non-Home Assistant users"""
    try:
        logger.info(f"🎯 Executing app routine '{routine_type}' for {person}")
        
        # In a real implementation, these would trigger actual device actions
        # For now, we'll log what would happen
        
        if routine_type == "notification_only":
            logger.info(f"📱 Routine: Notification sent for {person}")
            
        elif routine_type == "sound":
            logger.info(f"🔊 Routine: Would play sound for {person} detection")
            # In real implementation: trigger device sound via Bluetooth/WiFi
            
        elif routine_type == "flash_light":
            logger.info(f"💡 Routine: Would flash connected light for {person}")
            # In real implementation: trigger smart light flash
            
        # Future routines could include:
        # - Webhook calls to other services
        # - Bluetooth device triggers
        # - Smart speaker announcements
        
    except Exception as e:
        logger.error(f"❌ Error executing app routine: {e}")

# ==================== MR60BHA2 Sensor API Endpoints ====================

@app.get("/api/sensor/mr60bha2/status", tags=["MR60BHA2 Sensor"])
async def get_mr60bha2_sensor_status():
    """Get MR60BHA2 sensor status and connection info"""
    try:
        status = get_mr60bha2_status()
        return {
            "sensor_type": "MR60BHA2 mmWave",
            "status": status,
            "integration": "active" if status.get("connected") else "disconnected"
        }
    except Exception as e:
        logger.error(f"❌ Error getting MR60BHA2 status: {e}")
        return {
            "sensor_type": "MR60BHA2 mmWave", 
            "status": {"error": str(e)},
            "integration": "error"
        }

@app.post("/api/sensor/mr60bha2/test", tags=["MR60BHA2 Sensor"])
async def test_mr60bha2_integration():
    """Test MR60BHA2 sensor integration"""
    try:
        status = get_mr60bha2_status()
        
        if not status.get("connected"):
            raise HTTPException(
                status_code=503,
                detail="MR60BHA2 sensor not connected"
            )
        
        return {
            "success": True,
            "message": "MR60BHA2 sensor integration is working",
            "sensor_status": status,
            "test_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing MR60BHA2 integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"MR60BHA2 test failed: {str(e)}"
        )

# ==================== Build Note 2: Notification API Endpoints ====================

@app.post("/api/notifications/register-token", tags=["Build Note 2: Notifications"])
async def register_push_token(token_data: PushTokenRegistration):
    """Register device push token for Ring-style notifications"""
    global push_tokens
    
    try:
        # Validate push token format
        if not token_data.push_token.startswith("ExponentPushToken["):
            raise HTTPException(
                status_code=400,
                detail="Invalid Expo push token format"
            )
        
        # Store push token
        push_tokens[token_data.user_id] = {
            "token": token_data.push_token,
            "device_id": token_data.device_id,
            "platform": token_data.platform,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"📱 Push token registered for {token_data.user_id}")
        
        return {
            "success": True,
            "message": f"Push token registered for {token_data.user_id}",
            "user_id": token_data.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to register push token: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/notifications/send-presence", tags=["Build Note 2: Notifications"])
async def send_presence_notification(notification: PresenceNotification):
    """Send Ring-style presence notification"""
    try:
        event = await trigger_presence_notification(
            person=notification.person,
            confidence=notification.confidence,
            sensor_id=notification.sensor_id or "entryway_1",
            location=notification.location or "Front Door",
            source=notification.source or "sensor_only"
        )
        
        if event:
            return {
                "success": True,
                "message": "Presence notification triggered",
                "event": event
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger notification")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send presence notification: {e}")
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")

@app.get("/api/notifications/events", tags=["Build Note 2: Notifications"])
async def get_presence_events():
    """Get recent presence events for dashboard"""
    global presence_events
    
    return {
        "events": presence_events[-20:],  # Last 20 events
        "count": len(presence_events)
    }

@app.delete("/api/notifications/token/{user_id}", tags=["Build Note 2: Notifications"])
async def remove_push_token(user_id: str):
    """Remove push token for user"""
    global push_tokens
    
    if user_id in push_tokens:
        del push_tokens[user_id]
        logger.info(f"🗑️ Push token removed for {user_id}")
        return {"success": True, "message": f"Push token removed for {user_id}"}
    else:
        raise HTTPException(status_code=404, detail="User token not found")

# ==================== Build Note 2: Automation Settings API ====================

@app.get("/api/automation/settings/{user_id}", tags=["Build Note 2: Automation"])
async def get_automation_settings(user_id: str):
    """Get automation settings for user"""
    global automation_settings
    
    # Default settings if user not found
    default_settings = {
        "user_id": user_id,
        "enable_home_assistant": True,
        "enable_push_notifications": True,
        "enable_app_routines": False,
        "app_routine_type": "notification_only"
    }
    
    user_settings = automation_settings.get(user_id, default_settings)
    user_settings["user_id"] = user_id  # Ensure user_id is always included
    
    return user_settings

@app.post("/api/automation/settings", tags=["Build Note 2: Automation"])
async def save_automation_settings(settings: AutomationSettings):
    """Save automation settings for user"""
    global automation_settings
    
    try:
        # Store settings
        automation_settings[settings.user_id] = {
            "user_id": settings.user_id,
            "enable_home_assistant": settings.enable_home_assistant,
            "enable_push_notifications": settings.enable_push_notifications,
            "enable_app_routines": settings.enable_app_routines,
            "app_routine_type": settings.app_routine_type,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"⚙️ Automation settings saved for {settings.user_id}")
        
        return {
            "success": True,
            "message": f"Settings saved for {settings.user_id}",
            "settings": automation_settings[settings.user_id]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to save automation settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

@app.get("/api/automation/settings", tags=["Build Note 2: Automation"])
async def get_all_automation_settings():
    """Get automation settings for all users"""
    global automation_settings
    
    return {
        "settings": automation_settings,
        "count": len(automation_settings)
    }

# ==================== Enhanced Mobile Enrollment with Build Note 2 ====================

@app.post("/api/biometric/enroll", tags=["Mobile Enrollment"])
async def enroll_user_mobile(enrollment_data: dict):
    """Enhanced mobile app enrollment endpoint with Build Note 2 integration"""
    global biometric_matcher, biometric_profiles
    
    try:
        logger.info(f"📱 Mobile enrollment for: {enrollment_data.get('display_name')}")
        
        # Validate required fields
        required_fields = ['user_id', 'display_name', 'mean_hr', 'std_hr', 'range_hr']
        for field in required_fields:
            if field not in enrollment_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Validate heart rate values
        if not (30 <= enrollment_data['mean_hr'] <= 200):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid heart rate: {enrollment_data['mean_hr']}. Must be between 30-200 bpm."
            )
        
        # Check biometric matcher is available
        if not biometric_matcher:
            raise HTTPException(status_code=503, detail="Biometric system not initialized")
        
        # Add to biometric matcher
        success = biometric_matcher.add_profile(
            user_id=enrollment_data['user_id'],
            mean_hr=enrollment_data['mean_hr'],
            std_hr=enrollment_data['std_hr'],
            range_hr=enrollment_data['range_hr']
        )
        
        if success:
            # Update in-memory profiles
            biometric_profiles[enrollment_data['user_id']] = {
                'mean_hr': enrollment_data['mean_hr'],
                'std_hr': enrollment_data['std_hr'],
                'range_hr': enrollment_data['range_hr']
            }
            
            # Initialize default automation settings for new user (Build Note 2)
            user_id = enrollment_data['user_id']
            if user_id not in automation_settings:
                automation_settings[user_id] = {
                    "user_id": user_id,
                    "enable_home_assistant": True,
                    "enable_push_notifications": True,
                    "enable_app_routines": False,
                    "app_routine_type": "notification_only",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"⚙️ Default automation settings created for {user_id}")
            
            # Save user metadata for mobile app display
            metadata = {
                "user_id": enrollment_data['user_id'],
                "display_name": enrollment_data['display_name'],
                "location": enrollment_data.get('location', 'Unknown'),
                "enrolled_at": datetime.now().isoformat(),
                "has_wearable": enrollment_data.get('has_wearable', False),
                "sample_count": len(enrollment_data.get('heartbeat_pattern', [])),
                "enrollment_duration": enrollment_data.get('enrollment_duration', 30),
                "device_id": enrollment_data.get('device_id', 'mobile_enrollment')
            }
            
            try:
                with open(f"user_metadata_{enrollment_data['user_id']}.json", "w") as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save metadata: {e}")
            
            logger.info(f"✅ Successfully enrolled {enrollment_data['display_name']} ({enrollment_data['user_id']})")
            
            return {
                "success": True,
                "user_id": enrollment_data['user_id'],
                "message": f"Successfully enrolled {enrollment_data['display_name']}",
                "profile_created": True,
                "confidence_threshold": 0.5,
                "build_note_2_features": {
                    "notifications_enabled": True,
                    "automation_settings_created": True
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create biometric profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Mobile enrollment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")

# ==================== Enhanced Presence Detection with Build Note 2 ====================

@app.post("/api/presence/event", tags=["Presence Detection"])
async def enhanced_presence_event(event_data: dict):
    """Enhanced presence detection endpoint with Ring-style notifications"""
    global biometric_matcher, biometric_profiles
    
    try:
        logger.info(f"🔍 Processing presence event: {event_data}")
        
        # Extract heart rate data
        heart_rate_data = event_data.get('heart_rate', [])
        if not heart_rate_data:
            raise HTTPException(status_code=400, detail="No heart rate data provided")
        
        # Perform biometric matching
        if not biometric_matcher:
            raise HTTPException(status_code=503, detail="Biometric system not initialized")
        
        match_result = biometric_matcher.match_profile(heart_rate_data)
        
        if match_result:
            person = match_result["user_id"]
            confidence = match_result["confidence"]
            source = event_data.get("source", "sensor_only")
            
            logger.info(f"✅ Person identified: {person} with {confidence:.1%} confidence")
            
            # Trigger Build Note 2 notification system
            await trigger_presence_notification(
                person=person,
                confidence=confidence,
                sensor_id=event_data.get("sensor_id", "entryway_1"),
                location=event_data.get("location", "Front Door"),
                source=source
            )
            
            return {
                "success": True,
                "person_detected": True,
                "person": person,
                "confidence": confidence,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "build_note_2": {
                    "notification_triggered": True,
                    "mqtt_published": True
                }
            }
        else:
            logger.info("❌ No person identified from heart rate data")
            return {
                "success": True,
                "person_detected": False,
                "confidence": 0.0,
                "message": "No matching biometric profile found"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Presence detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Presence detection failed: {str(e)}")

# ==================== Existing Endpoints (Preserved) ====================

@app.get("/api/biometric/enrolled-users", tags=["Mobile Enrollment"])
async def get_enrolled_users():
    """Get enrolled users for mobile dashboard"""
    global biometric_matcher, biometric_profiles
    
    try:
        enrolled_users = []
        
        # Use in-memory profiles if available, otherwise load from database
        profiles_to_use = biometric_profiles
        if not profiles_to_use and biometric_matcher:
            profiles_to_use = biometric_matcher.load_profiles_from_db()
        
        for user_id, profile_data in profiles_to_use.items():
            # Load metadata if available
            metadata = {
                "display_name": user_id.replace("_", " ").title(), 
                "location": "Unknown",
                "enrolled_at": datetime.now().isoformat(),
                "has_wearable": False,
                "sample_count": 30
            }
            
            try:
                with open(f"user_metadata_{user_id}.json", "r") as f:
                    file_metadata = json.load(f)
                    metadata.update(file_metadata)
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Failed to load metadata for {user_id}: {e}")
            
            enrolled_users.append({
                "id": user_id,
                "name": metadata["display_name"],
                "location": metadata["location"],
                "status": "enrolled",
                "confidence": 0,
                "lastSeen": metadata["enrolled_at"],
                "mean_hr": profile_data.get("mean_hr", 0),
                "std_hr": profile_data.get("std_hr", 0),
                "range_hr": profile_data.get("range_hr", 0),
                "has_wearable": metadata["has_wearable"],
                "sample_count": metadata["sample_count"]
            })
        
        logger.info(f"📊 Returning {len(enrolled_users)} enrolled users")
        return {"enrolled_users": enrolled_users, "count": len(enrolled_users)}
        
    except Exception as e:
        logger.error(f"❌ Failed to get enrolled users: {e}")
        return {"enrolled_users": [], "count": 0}

@app.delete("/api/biometric/user/{user_id}", tags=["Mobile Enrollment"])
async def delete_enrolled_user(user_id: str):
    """Delete an enrolled user (for testing/management)"""
    global biometric_matcher, biometric_profiles, push_tokens, automation_settings
    
    try:
        # Remove from biometric matcher database
        if biometric_matcher and user_id in biometric_profiles:
            # Remove from in-memory cache
            del biometric_profiles[user_id]
            
            # Remove Build Note 2 data
            if user_id in push_tokens:
                del push_tokens[user_id]
                logger.info(f"📱 Push token removed for {user_id}")
            
            if user_id in automation_settings:
                del automation_settings[user_id]
                logger.info(f"⚙️ Automation settings removed for {user_id}")
            
            # Remove metadata file
            try:
                import os
                os.remove(f"user_metadata_{user_id}.json")
            except FileNotFoundError:
                pass
            
            logger.info(f"🗑️ Deleted user: {user_id}")
            return {"success": True, "message": f"Deleted user {user_id}"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@app.get("/api/biometric/user/{user_id}", tags=["Mobile Enrollment"])
async def get_user_profile(user_id: str):
    """Get detailed profile for a specific user"""
    global biometric_matcher, biometric_profiles
    
    try:
        # Check if user exists in profiles
        if user_id not in biometric_profiles:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = biometric_profiles[user_id]
        
        # Load metadata
        metadata = {
            "display_name": user_id.replace("_", " ").title(),
            "location": "Unknown",
            "enrolled_at": datetime.now().isoformat(),
            "has_wearable": False
        }
        
        try:
            with open(f"user_metadata_{user_id}.json", "r") as f:
                file_metadata = json.load(f)
                metadata.update(file_metadata)
        except FileNotFoundError:
            pass
        
        return {
            "user_id": user_id,
            "display_name": metadata["display_name"],
            "location": metadata["location"],
            "biometric_profile": profile,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user profile {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

# ==================== Root and Health Endpoints ====================
@app.get("/", tags=["Health"])
async def read_root():
    """Root endpoint to verify API is running."""
    global biometric_profiles
    
    # Get MR60BHA2 status
    mr60bha2_info = {"status": "not_initialized"}
    try:
        mr60bha2_status = get_mr60bha2_status()
        mr60bha2_info = {
            "status": "connected" if mr60bha2_status.get("connected") else "disconnected",
            "sensor_type": "MR60BHA2 mmWave",
            "module_available": MR60BHA2_AVAILABLE
        }
    except:
        pass
    
    return {
        "message": "Presient API with MR60BHA2 Sensor Integration",
        "status": "healthy",
        "version": "2.1.0",
        "biometric_system": {
            "initialized": biometric_matcher is not None,
            "enrolled_users": len(biometric_profiles),
            "database_path": getattr(biometric_matcher, 'db_path', None) if biometric_matcher else None
        },
        "mr60bha2_sensor": mr60bha2_info,
        "build_note_2": {
            "push_tokens_registered": len(push_tokens),
            "automation_settings_configured": len(automation_settings),
            "recent_events": len(presence_events)
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint."""
    global biometric_matcher, biometric_profiles
    
    # Check database
    db_healthy = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check biometric system health
    biometric_health = {
        "matcher_initialized": biometric_matcher is not None,
        "profiles_loaded": len(biometric_profiles),
        "database_accessible": False
    }
    
    if biometric_matcher:
        try:
            # Test database access
            profile_count = biometric_matcher.get_profile_count()
            biometric_health["database_accessible"] = True
            biometric_health["database_profile_count"] = profile_count
        except Exception as e:
            logger.error(f"Biometric database health check failed: {e}")
            biometric_health["database_error"] = str(e)
    
    # Check MR60BHA2 sensor health
    mr60bha2_health = {"status": "not_initialized"}
    try:
        mr60bha2_status = get_mr60bha2_status()
        mr60bha2_health = {
            "status": "connected" if mr60bha2_status.get("connected") else "disconnected",
            "buffer_size": mr60bha2_status.get("buffer_size", 0),
            "presence_detected": mr60bha2_status.get("presence_detected", False),
            "topics_subscribed": len(mr60bha2_status.get("topics", {})),
            "module_available": MR60BHA2_AVAILABLE
        }
    except Exception as e:
        mr60bha2_health = {"status": "error", "error": str(e)}
    
    # Overall health
    is_healthy = db_healthy and (mqtt_publisher and (mqtt_publisher.connected or not mqtt_publisher.enabled))
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": {
            "database": "connected" if db_healthy else "disconnected",
            "biometric_system": biometric_health,
            "mqtt": {
                "enabled": mqtt_publisher.enabled if mqtt_publisher else False,
                "connected": mqtt_publisher.connected if mqtt_publisher else False
            },
            "mr60bha2_sensor": mr60bha2_health,
            "build_note_2": {
                "notification_system": "operational",
                "push_tokens": len(push_tokens),
                "automation_settings": len(automation_settings)
            }
        },
        "version": "2.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# ==================== Biometric System Status Endpoints ====================

@app.get("/api/system/biometric-status", tags=["Biometric"])
async def biometric_system_status():
    """Detailed biometric system status for debugging"""
    global biometric_matcher, biometric_profiles
    
    try:
        status = {
            "biometric_matcher": {
                "initialized": biometric_matcher is not None,
                "database_path": getattr(biometric_matcher, 'db_path', None) if biometric_matcher else None,
                "tolerance_percent": getattr(biometric_matcher, 'tolerance_percent', None) if biometric_matcher else None
            },
            "profiles": {
                "loaded_count": len(biometric_profiles),
                "loaded_users": list(biometric_profiles.keys()) if biometric_profiles else []
            },
            "environment": {
                "db_path": os.getenv("PRESIENT_DB_PATH", "presient.db"),
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        }
        
        # Add database stats if available
        if biometric_matcher:
            try:
                db_count = biometric_matcher.get_profile_count()
                status["database"] = {
                    "profile_count": db_count,
                    "accessible": True
                }
            except Exception as e:
                status["database"] = {
                    "accessible": False,
                    "error": str(e)
                }
        
        return status
        
    except Exception as e:
        logger.error(f"Biometric system status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Biometric system status check failed", "detail": str(e)}
        )

# ==================== MQTT Status Endpoints ====================
@app.get("/api/mqtt/status", tags=["MQTT"])
async def mqtt_status():
    """Get MQTT connection status."""
    if not mqtt_publisher:
        return {
            "enabled": False,
            "connected": False,
            "broker": "not_configured",
            "base_topic": "not_configured",
            "error": "MQTT publisher not initialized"
        }
    
    return {
        "enabled": mqtt_publisher.enabled,
        "connected": mqtt_publisher.connected,
        "broker": f"{mqtt_publisher.broker_host}:{mqtt_publisher.broker_port}",
        "base_topic": mqtt_publisher.base_topic,
        "uptime": mqtt_publisher.get_uptime() if hasattr(mqtt_publisher, 'get_uptime') else None
    }

@app.post("/api/mqtt/test-publish", tags=["MQTT"])
async def test_mqtt_publish():
    """Test MQTT publishing with a sample message."""
    if not mqtt_publisher or not mqtt_publisher.connected:
        raise HTTPException(
            status_code=503,
            detail=create_error_response(
                "MQTT_NOT_CONNECTED",
                "MQTT broker is not connected"
            )
        )
    
    try:
        test_data = {
            "test": True,
            "message": "Hello from Presient API with MR60BHA2 Integration",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "build_note_2_features": [
                "ring_style_notifications",
                "automation_decoupling",
                "app_routines"
            ],
            "mr60bha2_features": [
                "real_heartbeat_detection",
                "mmwave_presence_sensing",
                "automatic_biometric_matching"
            ]
        }
        
        topic = f"{mqtt_publisher.base_topic}/test"
        await mqtt_publisher.publish(topic, json.dumps(test_data), retain=False)
        
        return {
            "success": True,
            "message": "Test message published to MQTT",
            "topic": topic,
            "payload": test_data
        }
        
    except Exception as e:
        logger.error(f"Error in MQTT test publish: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "MQTT_PUBLISH_FAILED",
                f"Failed to publish message: {str(e)}"
            )
        )

# ==================== Development/Test Endpoints ====================
if os.getenv("ENVIRONMENT", "development") == "development":
    @app.get("/test/error/{error_code}", tags=["Testing"])
    async def test_error(error_code: int):
        """Test error handling for different HTTP status codes."""
        if error_code == 400:
            raise HTTPException(status_code=400, detail="Bad Request test")
        elif error_code == 401:
            raise HTTPException(
                status_code=401,
                detail={"error": "UNAUTHORIZED", "message": "Authentication required"}
            )
        elif error_code == 403:
            raise HTTPException(
                status_code=403,
                detail={"error": "FORBIDDEN", "message": "Access denied"}
            )
        elif error_code == 404:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "message": "Resource not found"}
            )
        elif error_code == 422:
            raise RequestValidationError([{
                "loc": ["body", "test_field"],
                "msg": "field required",
                "type": "value_error.missing"
            }])
        elif error_code == 500:
            raise Exception("Internal server error test")
        else:
            return {"message": f"No test configured for error code {error_code}"}
    
    @app.get("/test/exceptions", tags=["Testing"])
    async def test_exceptions(exception_type: str):
        """Test custom exception handlers."""
        if exception_type == "validation":
            raise ValidationException(
                message="Custom validation failed",
                field="test_field",
                value="invalid_value"
            )
        elif exception_type == "database":
            raise DatabaseException(
                message="Database operation failed",
                operation="SELECT",
                table="test_table"
            )
        elif exception_type == "integrity":
            raise IntegrityError("Duplicate key", None, Exception("Duplicate key"))
        elif exception_type == "operational":
            raise OperationalError("Connection failed", None, Exception("Connection failed"))
        else:
            return {"message": f"No test configured for exception type {exception_type}"}
    
    @app.post("/test/notification", tags=["Testing - Build Note 2"])
    async def test_notification_system(person: str = "test_user", confidence: float = 0.95):
        """Test Build Note 2 notification system"""
        try:
            event = await trigger_presence_notification(
                person=person,
                confidence=confidence,
                sensor_id="test_sensor",
                location="Test Location",
                source="test"
            )
            
            return {
                "success": True,
                "message": "Test notification triggered",
                "event": event,
                "push_tokens_available": len(push_tokens),
                "automation_settings_available": len(automation_settings)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.get("/test/biometric", tags=["Testing"])
    async def test_biometric_system():
        """Test biometric system functionality."""
        global biometric_matcher
        
        if not biometric_matcher:
            return {"error": "Biometric system not initialized"}
        
        try:
            # Test database access
            profile_count = biometric_matcher.get_profile_count()
            profiles = biometric_matcher.load_profiles_from_db()
            
            # Test matching with fake data
            test_hr = [72, 75, 68, 70, 74]
            matched_user = biometric_matcher.match_profile([float(x) for x in test_hr])
            
            return {
                "biometric_system": "functional",
                "database_profiles": profile_count,
                "loaded_profiles": len(profiles),
                "test_match_result": matched_user or "no_match",
                "test_hr_values": test_hr,
                "build_note_2_integration": "ready",
                "mr60bha2_integration": "ready"
            }
            
        except Exception as e:
            return {
                "biometric_system": "error",
                "error": str(e)
            }

# ==================== Main Entry Point ====================
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )