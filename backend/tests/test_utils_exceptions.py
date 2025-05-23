# backend/tests/test_utils_exceptions.py
import pytest
import json
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.utils.exceptions import (
    CustomHTTPException,
    DatabaseException,
    ValidationException,
    http_error_handler,
    validation_error_handler,
    custom_database_error_handler,
    custom_validation_error_handler,
    general_exception_handler
)


class TestCustomExceptions:
    """Test suite for custom exception classes."""
    
    def test_custom_http_exception_creation(self):
        """Test creating CustomHTTPException with all parameters."""
        exc = CustomHTTPException(
            status_code=409,
            detail="Resource conflict",
            headers={"X-Custom": "header"},
            error_code="CONFLICT_001",
            context={"resource_id": "123"}
        )
        
        assert exc.status_code == 409
        assert exc.detail == "Resource conflict"
        assert exc.headers == {"X-Custom": "header"}
        assert exc.error_code == "CONFLICT_001"
        assert exc.context == {"resource_id": "123"}
    
    def test_custom_http_exception_minimal(self):
        """Test creating CustomHTTPException with minimal parameters."""
        exc = CustomHTTPException(status_code=400, detail="Bad request")
        
        assert exc.status_code == 400
        assert exc.detail == "Bad request"
        assert exc.headers is None
        assert exc.error_code is None
        assert exc.context == {}
    
    def test_database_exception_creation(self):
        """Test creating DatabaseException with all parameters."""
        exc = DatabaseException(
            message="Connection failed",
            operation="INSERT",
            table="users"
        )
        
        assert exc.message == "Connection failed"
        assert exc.operation == "INSERT"
        assert exc.table == "users"
        assert str(exc) == "Connection failed"
    
    def test_database_exception_minimal(self):
        """Test creating DatabaseException with minimal parameters."""
        exc = DatabaseException(message="Database error")
        
        assert exc.message == "Database error"
        assert exc.operation is None
        assert exc.table is None
    
    def test_validation_exception_creation(self):
        """Test creating ValidationException with all parameters."""
        exc = ValidationException(
            message="Invalid value",
            field="email",
            value="invalid-email"
        )
        
        assert exc.message == "Invalid value"
        assert exc.field == "email"
        assert exc.value == "invalid-email"
        assert str(exc) == "Invalid value"
    
    def test_validation_exception_minimal(self):
        """Test creating ValidationException with minimal parameters."""
        exc = ValidationException(message="Validation failed")
        
        assert exc.message == "Validation failed"
        assert exc.field is None
        assert exc.value is None


class TestExceptionHandlerFunctions:
    """Test suite for exception handler functions."""
    
    def create_mock_request(self, method="GET", url="http://test.com/test", client_host="127.0.0.1"):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = method
        request.url = Mock()
        request.url.__str__ = Mock(return_value=url)
        request.client = Mock()
        request.client.host = client_host
        request.headers = {"user-agent": "test-client"}
        return request
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_http_error_handler(self, mock_logger):
        """Test HTTP error handler function."""
        request = self.create_mock_request()
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await http_error_handler(request, exc)
        
        assert response.status_code == 404
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        assert content["error"]["status_code"] == 404
        assert content["error"]["message"] == "Not found"
        assert content["error"]["type"] == "http_error"
        
        # Verify logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "HTTP 404 error" in call_args[0][0]
        assert "extra" in call_args[1]
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_http_error_handler_with_custom_exception(self, mock_logger):
        """Test HTTP error handler with CustomHTTPException."""
        request = self.create_mock_request()
        exc = CustomHTTPException(
            status_code=409,
            detail="Conflict",
            error_code="CONFLICT_001",
            context={"field": "name"}
        )
        
        response = await http_error_handler(request, exc)
        
        assert response.status_code == 409
        
        content = json.loads(response.body.decode())
        assert content["error"]["status_code"] == 409
        assert content["error"]["message"] == "Conflict"
        assert content["error"]["code"] == "CONFLICT_001"
        assert content["error"]["context"] == {"field": "name"}
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_validation_error_handler(self, mock_logger):
        """Test validation error handler function."""
        request = self.create_mock_request(method="POST", url="http://test.com/api/test")
        
        # Create a mock validation error
        errors = [
            {
                "loc": ["body", "email"],
                "msg": "field required",
                "type": "value_error.missing",
                "input": None
            }
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = errors
        
        response = await validation_error_handler(request, exc)
        
        assert response.status_code == 422
        
        content = json.loads(response.body.decode())
        assert content["error"]["status_code"] == 422
        assert content["error"]["message"] == "Validation failed"
        assert content["error"]["type"] == "validation_error"
        assert "details" in content["error"]
        assert len(content["error"]["details"]) == 1
        assert content["error"]["details"][0]["field"] == "body.email"
        
        # Verify logging was called
        mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_database_error_handler(self, mock_logger):
        """Test database error handler function."""
        request = self.create_mock_request()
        exc = DatabaseException(
            message="Connection timeout",
            operation="SELECT",
            table="users"
        )
        
        response = await custom_database_error_handler(request, exc)
        
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        assert content["error"]["status_code"] == 500
        assert content["error"]["message"] == "Database operation failed"
        assert content["error"]["type"] == "database_error"
        assert content["error"]["details"]["operation"] == "SELECT"
        assert content["error"]["details"]["table"] == "users"
        
        # Verify logging was called
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_custom_validation_error_handler(self, mock_logger):
        """Test custom validation error handler function."""
        request = self.create_mock_request()
        exc = ValidationException(
            message="Invalid email format",
            field="email",
            value="invalid-email"
        )
        
        response = await custom_validation_error_handler(request, exc)
        
        assert response.status_code == 400
        
        content = json.loads(response.body.decode())
        assert content["error"]["status_code"] == 400
        assert content["error"]["message"] == "Invalid email format"
        assert content["error"]["type"] == "custom_validation_error"
        assert content["error"]["details"]["field"] == "email"
        assert content["error"]["details"]["value"] == "invalid-email"
        
        # Verify logging was called
        mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.utils.exceptions.logger')
    async def test_general_exception_handler(self, mock_logger):
        """Test general exception handler function."""
        request = self.create_mock_request()
        exc = ValueError("Something went wrong")
        
        response = await general_exception_handler(request, exc)
        
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        assert content["error"]["status_code"] == 500
        assert content["error"]["message"] == "Internal server error"
        assert content["error"]["type"] == "internal_error"
        
        # Verify critical logging was called with exc_info=True
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        assert call_args[1]["exc_info"] is True
    
    @pytest.mark.asyncio
    async def test_handler_with_no_client_info(self):
        """Test handlers work when request has no client info."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.__str__ = Mock(return_value="http://test.com/test")
        request.client = None  # No client info
        request.headers = {}
        
        exc = HTTPException(status_code=400, detail="Bad request")
        
        with patch('backend.utils.exceptions.logger') as mock_logger:
            response = await http_error_handler(request, exc)
            
            assert response.status_code == 400
            
            # Should not crash even without client info
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            extra = call_args[1]["extra"]
            assert extra["client_ip"] is None


class TestExceptionHandlerEdgeCases:
    """Test suite for edge cases in exception handling."""
    
    def create_mock_request(self, **kwargs):
        """Create a mock request with default values."""
        defaults = {
            "method": "GET",
            "url": "http://test.com/test",
            "client_host": "127.0.0.1"
        }
        defaults.update(kwargs)
        
        request = Mock(spec=Request)
        request.method = defaults["method"]
        request.url = Mock()
        request.url.__str__ = Mock(return_value=defaults["url"])
        
        if defaults["client_host"]:
            request.client = Mock()
            request.client.host = defaults["client_host"]
        else:
            request.client = None
            
        request.headers = {"user-agent": "test-client"}
        return request
    
    @pytest.mark.asyncio
    async def test_database_exception_without_operation_or_table(self):
        """Test database exception handler without operation or table."""
        request = self.create_mock_request()
        exc = DatabaseException(message="Generic database error")
        
        with patch('backend.utils.exceptions.logger') as mock_logger:
            response = await custom_database_error_handler(request, exc)
            
            content = json.loads(response.body.decode())
            assert content["error"]["details"] is None  # No operation/table provided
    
    @pytest.mark.asyncio
    async def test_validation_exception_without_field_or_value(self):
        """Test validation exception handler without field or value."""
        request = self.create_mock_request()
        exc = ValidationException(message="Generic validation error")
        
        with patch('backend.utils.exceptions.logger') as mock_logger:
            response = await custom_validation_error_handler(request, exc)
            
            content = json.loads(response.body.decode())
            assert content["error"]["details"] is None  # No field/value provided
    
    @pytest.mark.asyncio
    async def test_request_with_special_characters_in_url(self):
        """Test handler with special characters in URL."""
        request = self.create_mock_request(
            url="http://test.com/test?param=value%20with%20spaces&other=üñíçødé"
        )
        exc = HTTPException(status_code=400, detail="Bad request")
        
        with patch('backend.utils.exceptions.logger') as mock_logger:
            response = await http_error_handler(request, exc)
            
            assert response.status_code == 400
            # Should handle special characters without crashing
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_very_long_error_message(self):
        """Test handler with very long error message."""
        long_message = "x" * 10000  # Very long message
        request = self.create_mock_request()
        exc = HTTPException(status_code=400, detail=long_message)
        
        with patch('backend.utils.exceptions.logger') as mock_logger:
            response = await http_error_handler(request, exc)
            
            assert response.status_code == 400
            content = json.loads(response.body.decode())
            assert content["error"]["message"] == long_message
            
            # Should handle long messages without issues
            mock_logger.error.assert_called_once()