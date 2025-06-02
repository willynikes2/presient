"""
Enhanced main.py with auth integration, improved structure, and SQLite biometric authentication
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
    title="Presient API",
    description="Biometric presence authentication system using mmWave heartbeat recognition with SQLite storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # Use lifespan instead of deprecated startup/shutdown events
)

# ==================== Middleware ====================
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),  # In production, use specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Custom Error Response ====================
def create_error_response(error_code: str, message: str, details: dict = None) -> dict:
    """Create standardized error response"""
    response = {
        "error": error_code,
        "message": message
    }
    if details:
        response["details"] = details
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
app.include_router(auth.router)  # Already has /api/auth prefix
app.include_router(profiles.router)  # Update prefix in router or here
app.include_router(presence.router)  # Update prefix in router or here
app.include_router(heartbeat_auth.router)  # Add this line

# ==================== Mobile Enrollment Endpoints ====================

@app.post("/api/biometric/enroll", tags=["Mobile Enrollment"])
async def enroll_user_mobile(enrollment_data: dict):
    """Mobile app enrollment endpoint"""
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
                import json
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
                "confidence_threshold": 0.5
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create biometric profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Mobile enrollment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")

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
                import json
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
    global biometric_matcher, biometric_profiles
    
    try:
        # Remove from biometric matcher database
        if biometric_matcher and user_id in biometric_profiles:
            # Note: You may need to implement delete functionality in your SQLiteBiometricMatcher
            # For now, we'll remove from in-memory cache
            del biometric_profiles[user_id]
            
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
            import json
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
    
    return {
        "message": "Presient API is running",
        "status": "healthy",
        "version": "1.0.0",
        "biometric_system": {
            "initialized": biometric_matcher is not None,
            "enrolled_users": len(biometric_profiles),
            "database_path": getattr(biometric_matcher, 'db_path', None) if biometric_matcher else None
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
    
    # Overall health
    is_healthy = db_healthy and (mqtt_publisher.connected or not mqtt_publisher.enabled)
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": {
            "database": "connected" if db_healthy else "disconnected",
            "biometric_system": biometric_health,
            "mqtt": {
                "enabled": mqtt_publisher.enabled,
                "connected": mqtt_publisher.connected
            }
        },
        "version": "1.0.0",
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
    if not mqtt_publisher.connected:
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
            "message": "Hello from Presient API",
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            raise IntegrityError("Duplicate key", None, None)
        elif exception_type == "operational":
            raise OperationalError("Connection failed", None, None)
        else:
            return {"message": f"No test configured for exception type {exception_type}"}
    
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
            matched_user = biometric_matcher.match_profile(test_hr)
            
            return {
                "biometric_system": "functional",
                "database_profiles": profile_count,
                "loaded_profiles": len(profiles),
                "test_match_result": matched_user or "no_match",
                "test_hr_values": test_hr
            }
            
        except Exception as e:
            return {
                "biometric_system": "error",
                "error": str(e)
            }

# ==================== Additional imports for proper functionality ====================
import json
from datetime import datetime, timezone

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