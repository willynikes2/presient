"""
Enhanced main.py with auth integration and improved structure
"""

import logging
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
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
    await shutdown_mqtt()

# ==================== Initialize FastAPI App ====================
app = FastAPI(
    title="Presient API",
    description="Biometric presence authentication system using mmWave heartbeat recognition",
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
from backend.routes import auth, presence, profiles

# Include routers with consistent prefixing
app.include_router(auth.router)  # Already has /api/auth prefix
app.include_router(profiles.router)  # Update prefix in router or here
app.include_router(presence.router)  # Update prefix in router or here

# ==================== Root and Health Endpoints ====================
@app.get("/", tags=["Health"])
async def read_root():
    """Root endpoint to verify API is running."""
    return {
        "message": "Presient API is running",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint."""
    # Check database
    db_healthy = False
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Overall health
    is_healthy = db_healthy and (mqtt_publisher.connected or not mqtt_publisher.enabled)
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": {
            "database": "connected" if db_healthy else "disconnected",
            "mqtt": {
                "enabled": mqtt_publisher.enabled,
                "connected": mqtt_publisher.connected
            }
        },
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

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