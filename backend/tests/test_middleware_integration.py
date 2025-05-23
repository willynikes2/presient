# backend/tests/test_middleware_integration.py
import pytest
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app


class TestMiddlewareIntegration:
    """Test suite for middleware order and integration."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_cors_middleware_present(self):
        """Test that CORS middleware is properly configured."""
        # Make a preflight request
        response = self.client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_cors_headers_on_error_response(self):
        """Test that CORS headers are included in error responses."""
        response = self.client.get(
            "/test/400",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 400
        
        # CORS headers should be present even on error responses
        assert "access-control-allow-origin" in response.headers
    
    def test_exception_handler_after_cors(self):
        """Test that exception handlers work correctly after CORS middleware."""
        # Test with a cross-origin request that triggers an exception
        response = self.client.get(
            "/test/500",
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 500
        
        # Response should have proper error format
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 500
        assert data["error"]["type"] == "internal_error"
        
        # CORS headers should still be present
        assert "access-control-allow-origin" in response.headers
    
    def test_validation_error_with_cors(self):
        """Test that validation errors work correctly with CORS."""
        response = self.client.post(
            "/presence/event",
            json={"invalid": "data"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 422
        
        # Response should have proper validation error format
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 422
        assert data["error"]["type"] == "validation_error"
        assert "details" in data["error"]
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_custom_exception_with_cors(self):
        """Test that custom exceptions work correctly with CORS."""
        response = self.client.get(
            "/test/custom-http",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 409
        
        # Response should have proper custom error format
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 409
        assert data["error"]["code"] == "RESOURCE_CONFLICT"
        assert "context" in data["error"]
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestApplicationStartup:
    """Test suite for application startup and configuration."""
    
    def test_app_instance_type(self):
        """Test that app is properly configured FastAPI instance."""
        assert isinstance(app, FastAPI)
        assert app.title == "Presient API"
        assert app.version == "1.0.0"
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured."""
        # Check that CORSMiddleware is in the middleware stack
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
        assert CORSMiddleware in middleware_types
    
    def test_exception_handlers_registered(self):
        """Test that exception handlers are properly registered."""
        # Check that exception handlers are registered
        assert len(app.exception_handlers) > 0
        
        # Check for specific exception types in handlers
        handler_keys = list(app.exception_handlers.keys())
        
        # Should have handlers for common HTTP exceptions
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        from fastapi import HTTPException
        
        assert RequestValidationError in handler_keys
        assert StarletteHTTPException in handler_keys or HTTPException in handler_keys
    
    def test_routes_registered(self):
        """Test that all expected routes are registered."""
        routes = [route.path for route in app.routes]
        
        # Check for main endpoints
        assert "/" in routes
        assert "/health" in routes
        
        # Check for test endpoints
        assert "/test/400" in routes
        assert "/test/422" in routes
        assert "/test/500" in routes
        assert "/test/custom-validation" in routes
        assert "/test/database-error" in routes
        assert "/test/custom-http" in routes


class TestErrorResponseFormat:
    """Test suite for consistent error response formatting."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_http_error_response_format(self):
        """Test HTTP error response has consistent format."""
        response = self.client.get("/test/400")
        data = response.json()
        
        # Check required error structure
        assert "error" in data
        error = data["error"]
        
        assert "status_code" in error
        assert "message" in error
        assert "type" in error
        assert "timestamp" in error
        
        assert isinstance(error["status_code"], int)
        assert isinstance(error["message"], str)
        assert isinstance(error["type"], str)
    
    def test_validation_error_response_format(self):
        """Test validation error response has consistent format."""
        response = self.client.post("/presence/event", json={})
        data = response.json()
        
        # Check required error structure
        assert "error" in data
        error = data["error"]
        
        assert "status_code" in error
        assert "message" in error
        assert "type" in error
        assert "details" in error
        assert "timestamp" in error
        
        assert error["status_code"] == 422
        assert error["type"] == "validation_error"
        assert isinstance(error["details"], list)
        
        # Check details format
        if error["details"]:
            detail = error["details"][0]
            assert "field" in detail
            assert "message" in detail
            assert "type" in detail
    
    def test_custom_error_response_format(self):
        """Test custom error response has consistent format with additional fields."""
        response = self.client.get("/test/custom-http")
        data = response.json()
        
        # Check required error structure
        assert "error" in data
        error = data["error"]
        
        assert "status_code" in error
        assert "message" in error
        assert "type" in error
        assert "timestamp" in error
        
        # Check custom fields
        assert "code" in error
        assert "context" in error
        
        assert error["code"] == "RESOURCE_CONFLICT"
        assert isinstance(error["context"], dict)
    
    def test_database_error_response_format(self):
        """Test database error response has consistent format."""
        response = self.client.get("/test/database-error")
        data = response.json()
        
        # Check required error structure
        assert "error" in data
        error = data["error"]
        
        assert "status_code" in error
        assert "message" in error
        assert "type" in error
        assert "details" in error
        assert "timestamp" in error
        
        assert error["status_code"] == 500
        assert error["type"] == "database_error"
        assert isinstance(error["details"], dict)
        
        # Check database-specific details
        details = error["details"]
        assert "operation" in details
        assert "table" in details


class TestErrorHandlerOrder:
    """Test suite for exception handler execution order."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_specific_handler_before_general(self):
        """Test that specific handlers are called before general ones."""
        # Custom validation error should be handled by custom handler, not general
        response = self.client.get("/test/custom-validation")
        data = response.json()
        
        assert response.status_code == 400
        assert data["error"]["type"] == "custom_validation_error"
        # Should not be "internal_error" from general handler
    
    def test_database_error_specific_handler(self):
        """Test that database errors use specific handler."""
        response = self.client.get("/test/database-error")
        data = response.json()
        
        assert response.status_code == 500
        assert data["error"]["type"] == "database_error"
        # Should not be "internal_error" from general handler
        assert "details" in data["error"]
        assert "operation" in data["error"]["details"]
    
    def test_unhandled_exception_general_handler(self):
        """Test that unhandled exceptions use general handler."""
        response = self.client.get("/test/500")
        data = response.json()
        
        assert response.status_code == 500
        assert data["error"]["type"] == "internal_error"
        assert data["error"]["message"] == "Internal server error"
        # Should not expose internal exception details


# Performance and load testing helpers
class TestExceptionHandlerPerformance:
    """Test suite for exception handler performance."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_error_handler_response_time(self):
        """Test that error handlers respond quickly."""
        import time
        
        start_time = time.time()
        response = self.client.get("/test/400")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Error handling should be fast (< 1 second for simple errors)
        assert response_time < 1.0
        assert response.status_code == 400
    
    def test_multiple_error_requests(self):
        """Test handling multiple error requests in sequence."""
        test_endpoints = [
            "/test/400",
            "/test/custom-validation", 
            "/test/database-error",
            "/test/custom-http"
        ]
        
        responses = []
        for endpoint in test_endpoints:
            response = self.client.get(endpoint)
            responses.append(response)
            assert response.status_code in [400, 409, 500]
            
            # Each response should have proper error format
            data = response.json()
            assert "error" in data
            assert "status_code" in data["error"]
        
        # All requests should have been handled successfully
        assert len(responses) == len(test_endpoints)