# backend/tests/test_exception_handlers.py
import pytest
import json
import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from unittest.mock import patch, Mock
from io import StringIO

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.db import Base, get_db
from backend.utils.exceptions import (
    CustomHTTPException,
    DatabaseException,
    ValidationException
)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_exceptions.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestExceptionHandlers:
    """Test suite for custom exception handlers."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create a string buffer to capture log output
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.INFO)
        
        # Add handler to the root logger
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Remove the handler
        logging.getLogger().removeHandler(self.handler)
        self.log_capture.close()
    
    def get_log_contents(self) -> str:
        """Get the captured log contents."""
        return self.log_capture.getvalue()
    
    def test_400_bad_request_error(self):
        """Test 400 Bad Request error handling."""
        response = client.get("/test/400")
        
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 400
        assert data["error"]["message"] == "This is a test 400 error"
        assert data["error"]["type"] == "http_error"
        assert "timestamp" in data["error"]
        
        # Check that error was logged
        log_contents = self.get_log_contents()
        assert "HTTP 400 error on GET" in log_contents
        assert "test/400" in log_contents
    
    def test_422_validation_error(self):
        """Test 422 Validation error handling."""
        # Make a request that will trigger validation error
        response = client.post(
            "/presence/event",
            json={"invalid_field": "invalid_value"}  # Missing required fields
        )
        
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 422
        assert data["error"]["message"] == "Validation failed"
        assert data["error"]["type"] == "validation_error"
        assert "details" in data["error"]
        assert isinstance(data["error"]["details"], list)
        
        # Check that validation error was logged
        log_contents = self.get_log_contents()
        assert "Validation error on POST" in log_contents
    
    def test_500_internal_server_error(self):
        """Test 500 Internal Server Error handling."""
        response = client.get("/test/500")
        
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 500
        assert data["error"]["message"] == "Internal server error"
        assert data["error"]["type"] == "internal_error"
        assert "timestamp" in data["error"]
        
        # Check that exception was logged as critical
        log_contents = self.get_log_contents()
        assert "Unhandled exception on GET" in log_contents
        assert "test/500" in log_contents
    
    def test_custom_validation_error(self):
        """Test custom validation exception handling."""
        response = client.get("/test/custom-validation")
        
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 400
        assert data["error"]["message"] == "Custom validation failed"
        assert data["error"]["type"] == "custom_validation_error"
        assert "details" in data["error"]
        assert data["error"]["details"]["field"] == "test_field"
        assert data["error"]["details"]["value"] == "invalid_value"
        
        # Check that custom validation error was logged
        log_contents = self.get_log_contents()
        assert "Custom validation error on GET" in log_contents
        assert "test/custom-validation" in log_contents
    
    def test_database_error(self):
        """Test database exception handling."""
        response = client.get("/test/database-error")
        
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 500
        assert data["error"]["message"] == "Database operation failed"
        assert data["error"]["type"] == "database_error"
        assert "details" in data["error"]
        assert data["error"]["details"]["operation"] == "SELECT"
        assert data["error"]["details"]["table"] == "test_table"
        
        # Check that database error was logged
        log_contents = self.get_log_contents()
        assert "Database error on GET" in log_contents
        assert "test/database-error" in log_contents
    
    def test_custom_http_error_with_context(self):
        """Test custom HTTP exception with additional context."""
        response = client.get("/test/custom-http")
        
        assert response.status_code == 409
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 409
        assert data["error"]["message"] == "Resource conflict occurred"
        assert data["error"]["type"] == "http_error"
        assert data["error"]["code"] == "RESOURCE_CONFLICT"
        assert "context" in data["error"]
        assert data["error"]["context"]["resource_id"] == "12345"
        assert data["error"]["context"]["conflicting_field"] == "name"
        
        # Check that HTTP error was logged
        log_contents = self.get_log_contents()
        assert "HTTP 409 error on GET" in log_contents
        assert "test/custom-http" in log_contents
    
    def test_root_endpoint_success(self):
        """Test successful root endpoint (no error)."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Presient API is running"
        assert data["status"] == "healthy"
        
        # Check that access was logged
        log_contents = self.get_log_contents()
        assert "Root endpoint accessed" in log_contents
    
    def test_health_endpoint_success(self):
        """Test successful health endpoint (no error)."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["version"] == "1.0.0"
        
        # Check that access was logged
        log_contents = self.get_log_contents()
        assert "Health check endpoint accessed" in log_contents
    
    def test_nonexistent_endpoint_404(self):
        """Test 404 error for nonexistent endpoint."""
        response = client.get("/nonexistent/endpoint")
        
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 404
        assert data["error"]["type"] == "http_error"
        
        # Check that 404 error was logged
        log_contents = self.get_log_contents()
        assert "HTTP 404 error on GET" in log_contents
        assert "nonexistent/endpoint" in log_contents


class TestExceptionLogging:
    """Test suite specifically for exception logging functionality."""
    
    @patch('backend.utils.exceptions.logger')
    def test_http_error_logging_details(self, mock_logger):
        """Test that HTTP errors are logged with proper details."""
        response = client.get("/test/400")
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check the log message
        assert "HTTP 400 error on GET" in call_args[0][0]
        
        # Check the extra context
        extra = call_args[1]['extra']
        assert extra['status_code'] == 400
        assert extra['method'] == 'GET'
        assert 'test/400' in extra['url']
        assert extra['detail'] == "This is a test 400 error"
    
    @patch('backend.utils.exceptions.logger')
    def test_validation_error_logging_details(self, mock_logger):
        """Test that validation errors are logged with proper details."""
        # Make a request that will trigger validation error
        response = client.post("/presence/event", json={})
        
        # Verify logger.warning was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Check the log message
        assert "Validation error on POST" in call_args[0][0]
        
        # Check the extra context
        extra = call_args[1]['extra']
        assert extra['method'] == 'POST'
        assert 'presence/event' in extra['url']
        assert 'error_count' in extra
        assert 'errors' in extra
    
    @patch('backend.utils.exceptions.logger')
    def test_unhandled_exception_logging(self, mock_logger):
        """Test that unhandled exceptions are logged as critical."""
        response = client.get("/test/500")
        
        # Verify logger.critical was called
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        
        # Check the log message
        assert "Unhandled exception on GET" in call_args[0][0]
        
        # Check that exc_info=True was passed for stack trace
        assert call_args[1]['exc_info'] is True
        
        # Check the extra context
        extra = call_args[1]['extra']
        assert extra['method'] == 'GET'
        assert 'test/500' in extra['url']
        assert 'exception_type' in extra
        assert 'exception_message' in extra


# Cleanup
def teardown_module():
    """Cleanup after all tests."""
    if os.path.exists("test_exceptions.db"):
        os.remove("test_exceptions.db")