"""
Centralized error handling utilities for API
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base API Exception with status code"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


def handle_error(e: Exception, operation: str = "operation") -> tuple:
    """
    Centralized error handler that returns appropriate status code and error response
    
    Args:
        e: The exception to handle
        operation: Description of the operation that failed (for logging)
    
    Returns:
        tuple: (status_code, error_response_dict)
    """
    
    # Custom API Exception
    if isinstance(e, APIException):
        logger.warning(f"{operation} - API Exception: {e.message}")
        return e.status_code, {
            'status': 'failed',
            'message': e.message,
            'error': str(e),
            'error_code': e.error_code
        }
    
    # 400 - Bad Request (Validation errors)
    if isinstance(e, ValidationError):
        logger.warning(f"{operation} - Validation error: {str(e)}")
        return 400, {
            'status': 'failed',
            'message': 'Validation error',
            'error': str(e),
            'error_code': 'VALIDATION_ERROR'
        }
    
    # 400 - Integrity Error (Duplicate, constraint violations)
    if isinstance(e, IntegrityError):
        logger.warning(f"{operation} - Integrity error: {str(e)}")
        return 400, {
            'status': 'failed',
            'message': 'Data integrity error. Record may already exist or violates constraints',
            'error': str(e),
            'error_code': 'INTEGRITY_ERROR'
        }
    
    # 401 - Unauthorized (Token errors)
    if isinstance(e, (InvalidToken, TokenError)):
        logger.warning(f"{operation} - Token error: {str(e)}")
        return 401, {
            'status': 'failed',
            'message': 'Invalid or expired token',
            'error': str(e),
            'error_code': 'INVALID_TOKEN'
        }
    
    # 404 - Not Found
    if isinstance(e, ObjectDoesNotExist):
        logger.warning(f"{operation} - Object not found: {str(e)}")
        return 404, {
            'status': 'failed',
            'message': 'Requested resource not found',
            'error': str(e),
            'error_code': 'NOT_FOUND'
        }
        
    # 500 - Internal Server Error (Unexpected errors)
    logger.error(f"{operation} - Unexpected error: {str(e)}", exc_info=True)
    return 500, {
        'status': 'error',
        'message': f'An unexpected error occurred during {operation}',
        'error': str(e),
        'error_code': 'INTERNAL_ERROR'
    }


def api_response_handler(success_code: int = 200):
    """
    Decorator to handle API responses and errors uniformly
    
    Usage:
        @api_response_handler(201)
        def my_endpoint(request):
            # Your logic here
            return data  # Will be wrapped in success response
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # If function returns tuple (status, data), use it as-is
                if isinstance(result, tuple):
                    return result
                # Otherwise wrap in success response
                return success_code, {
                    'status': 'success',
                    'message': f'{func.__name__.replace("_", " ").title()} successful',
                    'data': result
                }
            except Exception as e:
                return handle_error(e, func.__name__)
        return wrapper
    return decorator