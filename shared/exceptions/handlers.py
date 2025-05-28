import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class APIException(Exception):
    """Base exception class cho API errors"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = 'An error occurred'
    
    def __init__(self, message=None, status_code=None):
        self.message = message or self.default_message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)

class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'Validation error'

class AuthenticationError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = 'Authentication required'

class PermissionError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = 'Permission denied'

class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = 'Resource not found'

def api_exception_handler(exc, context):
    """
    Custom exception handler cho API responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Handle specific error types
        if hasattr(exc, 'message'):
            custom_response_data['message'] = exc.message
        elif hasattr(exc, 'detail'):
            custom_response_data['message'] = str(exc.detail)
        
        response.data = custom_response_data
        
        # Log error
        logger.error(f"API Error: {exc} - Status: {response.status_code}")
    
    return response