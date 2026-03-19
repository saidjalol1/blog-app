"""
Custom middleware for logging and error handling.
"""

import logging
import traceback
from django.http import JsonResponse

logger = logging.getLogger('django.request')


class ErrorLoggingMiddleware:
    """
    Middleware to log all unhandled exceptions with stack traces.
    
    This middleware catches exceptions that bubble up from views and logs them
    with full stack traces to the error log before re-raising them for Django's
    default error handling.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Log exceptions with stack traces.
        
        Args:
            request: Django HttpRequest object
            exception: The exception that was raised
        
        Returns:
            None to allow Django's default exception handling to proceed
        """
        # Get the full stack trace
        stack_trace = traceback.format_exc()
        
        # Log the error with stack trace
        logger.error(
            f"Unhandled exception in {request.method} {request.path}: "
            f"{type(exception).__name__}: {str(exception)}\n"
            f"Stack trace:\n{stack_trace}",
            exc_info=True,
            extra={
                'request': request,
                'status_code': 500,
            }
        )
        
        # Return None to let Django's default error handling proceed
        # This ensures proper error pages are shown to users
        return None
