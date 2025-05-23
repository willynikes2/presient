#!/usr/bin/env python3
"""
Exception Handler Audit Script for Presient API

This script audits the exception handling setup and validates the integration.
Run this script to verify that all exception handlers are properly configured.
"""

import sys
import os
import logging
from typing import Dict, List, Any
import importlib

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from backend.main import app
    from backend.utils import exceptions
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi import HTTPException
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class ExceptionHandlerAuditor:
    """Audits the exception handler setup in the FastAPI application."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
    
    def audit_app_initialization(self) -> bool:
        """Audit FastAPI app initialization."""
        print("🔍 Auditing FastAPI app initialization...")
        
        if not isinstance(self.app, FastAPI):
            self.issues.append("App is not a FastAPI instance")
            return False
        
        # Check app configuration
        if not self.app.title:
            self.warnings.append("App title is not set")
        else:
            self.successes.append(f"App title: {self.app.title}")
        
        if not self.app.version:
            self.warnings.append("App version is not set")
        else:
            self.successes.append(f"App version: {self.app.version}")
        
        return True
    
    def audit_cors_middleware(self) -> bool:
        """Audit CORS middleware configuration."""
        print("🔍 Auditing CORS middleware...")
        
        cors_found = False
        middleware_stack = []
        
        for middleware in self.app.user_middleware:
            middleware_stack.append(type(middleware.cls).__name__)
            if isinstance(middleware.cls, type) and issubclass(middleware.cls, CORSMiddleware):
                cors_found = True
                self.successes.append("CORS middleware is configured")
                break
        
        if not cors_found:
            self.issues.append("CORS middleware is not configured")
            return False
        
        # Check middleware order (CORS should be early in the stack)
        print(f"   Middleware stack: {middleware_stack}")
        
        return True
    
    def audit_exception_handlers(self) -> bool:
        """Audit exception handler registration."""
        print("🔍 Auditing exception handlers...")
        
        if not self.app.exception_handlers:
            self.issues.append("No exception handlers are registered")
            return False
        
        expected_handlers = {
            RequestValidationError: "validation_error_handler",
            HTTPException: "http_error_handler", 
            StarletteHTTPException: "http_error_handler",
            Exception: "general_exception_handler"
        }
        
        registered_handlers = list(self.app.exception_handlers.keys())
        print(f"   Registered handlers for: {[h.__name__ if hasattr(h, '__name__') else str(h) for h in registered_handlers]}")
        
        # Check for required handlers
        for exc_type, handler_name in expected_handlers.items():
            if exc_type in registered_handlers:
                self.successes.append(f"Handler for {exc_type.__name__} is registered")
            else:
                self.warnings.append(f"Handler for {exc_type.__name__} is not registered")
        
        # Check for custom exception handlers
        try:
            from backend.utils.exceptions import DatabaseException, ValidationException
            
            if DatabaseException in registered_handlers:
                self.successes.append("Custom DatabaseException handler is registered")
            else:
                self.warnings.append("Custom DatabaseException handler is not registered")
            
            if ValidationException in registered_handlers:
                self.successes.append("Custom ValidationException handler is registered")
            else:
                self.warnings.append("Custom ValidationException handler is not registered")
                
        except ImportError:
            self.warnings.append("Custom exception classes not found")
        
        return True
    
    def audit_exception_handler_order(self) -> bool:
        """Audit exception handler registration order."""
        print("🔍 Auditing exception handler order...")
        
        handler_types = list(self.app.exception_handlers.keys())
        
        # General Exception handler should be last
        if Exception in handler_types:
            exception_index = handler_types.index(Exception)
            if exception_index != len(handler_types) - 1:
                self.warnings.append("Exception handler is not registered last (may catch specific exceptions)")
            else:
                self.successes.append("General Exception handler is registered last")
        
        return True
    
    def audit_logging_configuration(self) -> bool:
        """Audit logging configuration."""
        print("🔍 Auditing logging configuration...")
        
        # Check if logging is configured
        root_logger = logging.getLogger()
        
        if not root_logger.handlers:
            self.warnings.append("No logging handlers configured")
            return False
        
        # Check for stdout handler
        stdout_handler_found = False
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                if handler.stream.name == '<stdout>':
                    stdout_handler_found = True
                    self.successes.append("Stdout logging handler found")
                    break
        
        if not stdout_handler_found:
            self.warnings.append("No stdout logging handler found")
        
        # Check logging level
        if root_logger.level <= logging.INFO:
            self.successes.append(f"Logging level is appropriate: {logging.getLevelName(root_logger.level)}")
        else:
            self.warnings.append(f"Logging level might be too high: {logging.getLevelName(root_logger.level)}")
        
        return True
    
    def audit_exception_utils_module(self) -> bool:
        """Audit the exception utils module."""
        print("🔍 Auditing exception utils module...")
        
        try:
            # Check required functions exist
            required_functions = [
                'http_error_handler',
                'validation_error_handler',
                'custom_database_error_handler',
                'custom_validation_error_handler', 
                'general_exception_handler'
            ]
            
            for func_name in required_functions:
                if hasattr(exceptions, func_name):
                    self.successes.append(f"Function {func_name} exists")
                else:
                    self.issues.append(f"Function {func_name} is missing")
            
            # Check required exception classes exist
            required_classes = [
                'CustomHTTPException',
                'DatabaseException',
                'ValidationException'
            ]
            
            for class_name in required_classes:
                if hasattr(exceptions, class_name):
                    self.successes.append(f"Exception class {class_name} exists")
                else:
                    self.issues.append(f"Exception class {class_name} is missing")
            
            return True
            
        except Exception as e:
            self.issues.append(f"Error auditing exception utils module: {e}")
            return False
    
    def audit_test_endpoints(self) -> bool:
        """Audit test endpoints for exception handling."""
        print("🔍 Auditing test endpoints...")
        
        expected_test_endpoints = [
            "/test/400",
            "/test/422", 
            "/test/500",
            "/test/custom-validation",
            "/test/database-error",
            "/test/custom-http"
        ]
        
        app_routes = [route.path for route in self.app.routes]
        
        for endpoint in expected_test_endpoints:
            if endpoint in app_routes:
                self.successes.append(f"Test endpoint {endpoint} exists")
            else:
                self.warnings.append(f"Test endpoint {endpoint} is missing")
        
        return True
    
    def run_audit(self) -> Dict[str, Any]:
        """Run the complete audit."""
        print("🚀 Starting exception handler audit...\n")
        
        audit_results = {
            "app_initialization": self.audit_app_initialization(),
            "cors_middleware": self.audit_cors_middleware(),
            "exception_handlers": self.audit_exception_handlers(),
            "handler_order": self.audit_exception_handler_order(),
            "logging_configuration": self.audit_logging_configuration(),
            "exception_utils": self.audit_exception_utils_module(),
            "test_endpoints": self.audit_test_endpoints()
        }
        
        return {
            "results": audit_results,
            "issues": self.issues,
            "warnings": self.warnings,
            "successes": self.successes
        }
    
    def print_report(self, audit_data: Dict[str, Any]):
        """Print a formatted audit report."""
        print("\n" + "="*60)
        print("🔍 EXCEPTION HANDLER AUDIT REPORT")
        print("="*60)
        
        # Summary
        total_checks = len(audit_data["results"])
        passed_checks = sum(1 for result in audit_data["results"].values() if result)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total checks: {total_checks}")
        print(f"   Passed: {passed_checks}")
        print(f"   Failed: {total_checks - passed_checks}")
        print(f"   Success rate: {passed_checks/total_checks*100:.1f}%")
        
        # Issues
        if audit_data["issues"]:
            print(f"\n❌ CRITICAL ISSUES ({len(audit_data['issues'])}):")
            for issue in audit_data["issues"]:
                print(f"   • {issue}")
        
        # Warnings
        if audit_data["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(audit_data['warnings'])}):")
            for warning in audit_data["warnings"]:
                print(f"   • {warning}")
        
        # Successes
        if audit_data["successes"]:
            print(f"\n✅ SUCCESSES ({len(audit_data['successes'])}):")
            for success in audit_data["successes"]:
                print(f"   • {success}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if audit_data["issues"]:
            print("   • Fix all critical issues before deploying to production")
        if audit_data["warnings"]:
            print("   • Review warnings and consider implementing suggested improvements")
        if not audit_data["issues"] and not audit_data["warnings"]:
            print("   • Exception handling setup looks good!")
        
        print("\n" + "="*60)


def main():
    """Main audit function."""
    try:
        auditor = ExceptionHandlerAuditor(app)
        audit_data = auditor.run_audit()
        auditor.print_report(audit_data)
        
        # Exit with error code if there are critical issues
        if audit_data["issues"]:
            sys.exit(1)
        else:
            print("✅ Audit completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Audit failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()