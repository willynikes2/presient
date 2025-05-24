# backend/utils/exceptions.py
import logging
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

# Configure logger for exception handling
logger = logging.getLogger(__name__)


class CustomHTTPException(HTTPException):
    """Custom HTTP Exception with additional context."""
    
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        headers: dict = None,
        error_code: str = None,
        context: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.context = context or {}


class DatabaseException(Exception):
    """Custom exception for database-related errors."""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        self.message = message
        self.operation = operation
        self.table = table
        super().__init__(self.message)


class ValidationException(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


async def http_error_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """
    Global HTTP error handler with logging and traceback for debugging.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception that was raised
        
    Returns:
        JSONResponse with error details
    """
    # Log the exception with traceback for better debugging
    # Include traceback for all HTTP errors to help with debugging
    logger.error(
        f"HTTP {exc.status_code} error on {request.method} {request.url}: {exc.detail}",
        exc_info=True,  # Always include traceback for debugging
        extra={
            "status_code": exc.status_code,
            "method": request.method,
            "url": str(request.url),
            "detail": exc.detail,
            "headers": dict(request.headers) if hasattr(request, 'headers') else {},
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Prepare error response
    error_response = {
        "error": {
            "status_code": exc.status_code,
            "message": exc.detail,
            "type": "http_error",
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None
        }
    }
    
    # Add additional context for custom exceptions
    if isinstance(exc, CustomHTTPException):
        if exc.error_code:
            error_response["error"]["code"] = exc.error_code
        if exc.context:
            error_response["error"]["context"] = exc.context
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, 'headers', None)
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors (422 status) with traceback for debugging.
    
    Args:
        request: The FastAPI request object
        exc: The validation error that was raised
        
    Returns:
        JSONResponse with validation error details
    """
    # Log validation errors with traceback for debugging
    logger.warning(
        f"Validation error on {request.method} {request.url}: {len(exc.errors())} validation errors",
        exc_info=True,  # Include traceback for debugging validation issues
        extra={
            "method": request.method,
            "url": str(request.url),
            "error_count": len(exc.errors()),
            "errors": exc.errors(),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Format validation errors for response
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    error_response = {
        "error": {
            "status_code": 422,
            "message": "Validation failed",
            "type": "validation_error",
            "details": formatted_errors,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None
        }
    }
    
    return JSONResponse(status_code=422, content=error_response)


async def custom_database_error_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    """
    Handle custom database exceptions with traceback.
    
    Args:
        request: The FastAPI request object
        exc: The database exception that was raised
        
    Returns:
        JSONResponse with database error details
    """
    # Log database errors with full traceback for debugging
    logger.error(
        f"Database error on {request.method} {request.url}: {exc.message}",
        exc_info=True,  # Include traceback for database debugging
        extra={
            "method": request.method,
            "url": str(request.url),
            "operation": exc.operation,
            "table": exc.table,
            "message": exc.message,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = {
        "error": {
            "status_code": 500,
            "message": "Database operation failed",
            "type": "database_error",
            "details": {
                "operation": exc.operation,
                "table": exc.table
            } if exc.operation or exc.table else None,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None
        }
    }
    
    return JSONResponse(status_code=500, content=error_response)


async def custom_validation_error_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """
    Handle custom validation exceptions with traceback.
    
    Args:
        request: The FastAPI request object
        exc: The validation exception that was raised
        
    Returns:
        JSONResponse with validation error details
    """
    # Log custom validation errors with traceback for debugging
    logger.warning(
        f"Custom validation error on {request.method} {request.url}: {exc.message}",
        exc_info=True,  # Include traceback for validation debugging
        extra={
            "method": request.method,
            "url": str(request.url),
            "field": exc.field,
            "value": exc.value,
            "message": exc.message,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = {
        "error": {
            "status_code": 400,
            "message": exc.message,
            "type": "custom_validation_error",
            "details": {
                "field": exc.field,
                "value": exc.value
            } if exc.field else None,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None
        }
    }
    
    return JSONResponse(status_code=400, content=error_response)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions with full traceback.
    
    Args:
        request: The FastAPI request object
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Log unhandled exceptions as critical with full traceback
    logger.critical(
        f"Unhandled exception on {request.method} {request.url}: {str(exc)}",
        exc_info=True,  # Always include full traceback for unhandled exceptions
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = {
        "error": {
            "status_code": 500,
            "message": "Internal server error",
            "type": "internal_error",
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None
        }
    }
    
    return JSONResponse(status_code=500, content=error_response)
