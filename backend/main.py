# backend/main.py
import logging
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError

# Import database components
from backend.db import engine, Base

# Import models to register them (do this before creating tables)
import backend.models.profile
import backend.models.presence_events
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

# Create tables on startup
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables ready!")

# STEP 1: Initialize FastAPI app first
app = FastAPI(
    title="Presient API",
    description="Biometric presence authentication system using mmWave heartbeat recognition",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# STEP 2: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLAlchemy Exception Handlers
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity violations (unique constraints, foreign keys, etc.)"""
    logger.error(
        f"Database integrity error on {request.method} {request.url}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=409,  # Conflict
        content={
            "error": {
                "status_code": 409,
                "message": "Database integrity constraint violation",
                "type": "integrity_error",
                "details": {"error_type": "IntegrityError"}
            }
        }
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database operational errors (connection issues, timeouts, etc.)"""
    logger.error(
        f"Database operational error on {request.method} {request.url}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": {
                "status_code": 503,
                "message": "Database service temporarily unavailable",
                "type": "operational_error",
                "details": {"error_type": "OperationalError"}
            }
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle all other SQLAlchemy errors"""
    logger.error(
        f"SQLAlchemy error on {request.method} {request.url}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "status_code": 500,
                "message": "A database error occurred",
                "type": "sqlalchemy_error",
                "details": {"error_type": type(exc).__name__}
            }
        }
    )

# STEP 3: Add exception handlers (order matters - more specific first)
# Database-specific handlers are already added above

# Custom exception handlers
app.add_exception_handler(DatabaseException, custom_database_error_handler)
app.add_exception_handler(ValidationException, custom_validation_error_handler)

# Built-in FastAPI/Starlette exception handlers
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)

# General exception handler last (catches all unhandled exceptions)
app.add_exception_handler(Exception, general_exception_handler)

# Import and include routers after app setup
from backend.routes import presence, profiles

app.include_router(presence.router, prefix="/presence", tags=["presence"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])

@app.get("/")
async def read_root():
    """Root endpoint to verify API is running."""
    logger.info("Root endpoint accessed")
    return {"message": "Presient API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "database": "connected",
        "mqtt": "connected" if mqtt_publisher.connected else "disconnected",
        "version": "1.0.0"
    }

@app.get("/mqtt/status")
async def mqtt_status():
    """Get MQTT connection status."""
    logger.info("MQTT status endpoint accessed")
    return {
        "enabled": mqtt_publisher.enabled,
        "connected": mqtt_publisher.connected,
        "broker": f"{mqtt_publisher.broker_host}:{mqtt_publisher.broker_port}",
        "base_topic": mqtt_publisher.base_topic
    }

@app.post("/mqtt/test-publish")
async def test_mqtt_publish():
    """Test MQTT publishing with a sample message."""
    logger.info("MQTT test publish endpoint accessed")
    
    if not mqtt_publisher.connected:
        raise HTTPException(status_code=503, detail="MQTT not connected")
    
    try:
        test_data = {
            "test": True,
            "message": "Hello from Presient API",
            "timestamp": "2025-01-01T12:00:00Z"
        }
        
        await mqtt_publisher.publish(
            f"{mqtt_publisher.base_topic}/test",
            str(test_data),
            retain=False
        )
        
        return {
            "success": True,
            "message": "Test message published to MQTT",
            "topic": f"{mqtt_publisher.base_topic}/test"
        }
        
    except Exception as e:
        logger.error(f"Error in MQTT test publish: {e}")
        raise HTTPException(status_code=500, detail=f"MQTT publish failed: {str(e)}")

# Test endpoints for exception handling validation
@app.get("/test/400")
async def test_400_error():
    """Test endpoint for 400 Bad Request error."""
    logger.info("Test 400 error endpoint accessed")
    raise HTTPException(status_code=400, detail="This is a test 400 error")

@app.get("/test/422")
async def test_422_error():
    """Test endpoint for 422 Validation error."""
    logger.info("Test 422 error endpoint accessed")
    # This will be triggered by invalid query parameters
    raise RequestValidationError([{"loc": ["query", "test_param"], "msg": "field required", "type": "value_error.missing"}])

@app.get("/test/500")
async def test_500_error():
    """Test endpoint for 500 Internal Server error."""
    logger.info("Test 500 error endpoint accessed")
    raise Exception("This is a test unhandled exception")

@app.get("/test/custom-validation")
async def test_custom_validation_error():
    """Test endpoint for custom validation error."""
    logger.info("Test custom validation error endpoint accessed")
    raise ValidationException(
        message="Custom validation failed",
        field="test_field",
        value="invalid_value"
    )

@app.get("/test/database-error")
async def test_database_error():
    """Test endpoint for database error."""
    logger.info("Test database error endpoint accessed")
    raise DatabaseException(
        message="Failed to connect to database",
        operation="SELECT",
        table="test_table"
    )

@app.get("/test/custom-http")
async def test_custom_http_error():
    """Test endpoint for custom HTTP error with context."""
    logger.info("Test custom HTTP error endpoint accessed")
    raise CustomHTTPException(
        status_code=409,
        detail="Resource conflict occurred",
        error_code="RESOURCE_CONFLICT",
        context={"resource_id": "12345", "conflicting_field": "name"}
    )

@app.get("/test/sqlalchemy-integrity")
async def test_sqlalchemy_integrity_error():
    """Test endpoint for SQLAlchemy IntegrityError."""
    logger.info("Test SQLAlchemy IntegrityError endpoint accessed")
    raise IntegrityError("Duplicate key value violates unique constraint", None, None)

@app.get("/test/sqlalchemy-operational")
async def test_sqlalchemy_operational_error():
    """Test endpoint for SQLAlchemy OperationalError."""
    logger.info("Test SQLAlchemy OperationalError endpoint accessed")
    raise OperationalError("Connection to database failed", None, None)

@app.get("/test/sqlalchemy-general")
async def test_sqlalchemy_general_error():
    """Test endpoint for general SQLAlchemy error."""
    logger.info("Test SQLAlchemy general error endpoint accessed")
    raise SQLAlchemyError("General SQLAlchemy error occurred")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Presient API starting up...")
    logger.info("Exception handlers configured")
    logger.info("SQLAlchemy error handlers enabled")
    logger.info("CORS middleware enabled")
    logger.info("Database tables initialized")
    
    # Initialize MQTT
    await initialize_mqtt()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 Presient API shutting down...")
    
    # Cleanup MQTT
    await shutdown_mqtt()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)