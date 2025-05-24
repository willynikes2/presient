# backend/main.py
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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

# STEP 3: Add exception handlers (order matters - more specific first)
# Custom exception handlers first
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
        "version": "1.0.0"
    }

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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Presient API starting up...")
    logger.info("Exception handlers configured")
    logger.info("CORS middleware enabled")
    logger.info("Database tables initialized")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 Presient API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
