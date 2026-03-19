"""
Rate limiting utilities for spam prevention and abuse protection.

This module provides Redis-backed rate limiting for:
- Comment submissions
- Like/dislike actions
- Other user interactions
"""

import logging
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse

# Get security logger for rate limit violations
security_logger = logging.getLogger('django.security')


class RateLimiter:
    """Redis-backed rate limiter for preventing spam and abuse."""
    
    @staticmethod
    def check_rate_limit(identifier: str, action: str, limit: int, window: int, user_agent: str = None) -> bool:
        """
        Check if an action is within the rate limit.
        
        Args:
            identifier: Unique identifier (IP + visitor_id)
            action: Action type (e.g., 'comment', 'like', 'dislike')
            limit: Maximum number of actions allowed
            window: Time window in seconds
            user_agent: Optional user agent string for suspicious agent detection
        
        Returns:
            bool: True if within limit, False if exceeded
        """
        from blog.utils.helpers import is_suspicious_user_agent
        
        # Check if user agent is suspicious and apply stricter limits
        # Note: user_agent can be empty string (which is suspicious)
        if user_agent is not None and is_suspicious_user_agent(user_agent):
            # Apply 10x stricter rate limiting for suspicious agents
            limit = max(1, limit // 10)
            security_logger.warning(
                f"Suspicious user agent detected: action={action}, identifier={identifier}, "
                f"user_agent={user_agent[:100] if user_agent else '(empty)'}, stricter_limit={limit}"
            )
        
        # Include user agent hash in the key for better tracking
        key = f"ratelimit:{action}:{identifier}"
        if user_agent is not None:
            # Add user agent to identifier to prevent bypassing via UA changes
            import hashlib
            ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
            key = f"ratelimit:{action}:{identifier}:{ua_hash}"
        
        try:
            count = cache.get(key, 0)
            
            if count >= limit:
                # Log blocked request
                security_logger.warning(
                    f"Rate limit exceeded: action={action}, identifier={identifier}, "
                    f"count={count}, limit={limit}, window={window}s, "
                    f"user_agent={user_agent[:100] if user_agent else 'None'}"
                )
                return False
            
            # Increment counter
            cache.set(key, count + 1, window)
            return True
        except Exception as e:
            # If cache fails, allow the action but log the failure
            # Graceful degradation - don't block users due to cache issues
            security_logger.error(f"Rate limiter cache error: {str(e)}")
            return True
    
    @staticmethod
    def get_identifier(request) -> str:
        """
        Get unique identifier for rate limiting.
        
        Args:
            request: Django HttpRequest object
        
        Returns:
            str: Unique identifier combining IP and visitor ID
        """
        from blog.utils.cookie_manager import CookieManager
        return CookieManager.get_visitor_identifier(request)


def rate_limit(action: str, limit: int, window: int):
    """
    Decorator for view protection with rate limiting.
    
    Args:
        action: Action type identifier (e.g., 'comment', 'like')
        limit: Maximum number of actions allowed
        window: Time window in seconds
    
    Returns:
        Decorated view function that enforces rate limiting
    
    Example:
        @rate_limit('comment', limit=3, window=600)
        def submit_comment(request, slug):
            # ... comment submission logic
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            identifier = RateLimiter.get_identifier(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if not RateLimiter.check_rate_limit(identifier, action, limit, window, user_agent):
                # Log rate limit violation to security log
                from blog.utils.helpers import get_client_ip
                ip_address = get_client_ip(request)
                security_logger.warning(
                    f"Rate limit exceeded for {action}: identifier={identifier}, ip={ip_address}, "
                    f"limit={limit}, window={window}s, user_agent={user_agent[:100]}"
                )
                
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'You can only perform this action {limit} times per {window // 60} minutes. Please try again later.',
                    'retry_after': window
                }, status=429)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
