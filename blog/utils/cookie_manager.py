"""
Cookie management utilities for visitor identification and tracking.

This module provides centralized cookie management for:
- Visitor ID generation and retrieval
- View tracking per blog post
- Secure cookie attribute configuration
"""

import json
import uuid
from typing import Optional


class CookieManager:
    """Manages cookies for visitor identification and engagement tracking."""
    
    # Cookie names
    VISITOR_ID_COOKIE = 'visitor_id'
    VIEWED_POSTS_COOKIE = 'viewed_posts'
    
    # Cookie expiration durations (in seconds)
    VISITOR_ID_MAX_AGE = 365 * 24 * 60 * 60  # 365 days
    VIEWED_POSTS_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
    
    @staticmethod
    def get_or_create_visitor_id(request, response) -> str:
        """
        Get existing visitor ID from cookie or create a new one.
        
        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object (can be None for read-only)
        
        Returns:
            str: UUID4 visitor identifier
        """
        visitor_id = request.COOKIES.get(CookieManager.VISITOR_ID_COOKIE)
        
        if not visitor_id:
            # Generate new visitor ID
            visitor_id = str(uuid.uuid4())
            
            # Set cookie on response if provided
            if response is not None:
                response.set_cookie(
                    key=CookieManager.VISITOR_ID_COOKIE,
                    value=visitor_id,
                    max_age=CookieManager.VISITOR_ID_MAX_AGE,
                    httponly=True,
                    secure=True,
                    samesite='Lax'
                )
        
        return visitor_id
    
    @staticmethod
    def has_viewed_post(request, post_id: int) -> bool:
        """
        Check if visitor has already viewed a specific post.
        
        Args:
            request: Django HttpRequest object
            post_id: Blog post ID to check
        
        Returns:
            bool: True if post has been viewed, False otherwise
        """
        viewed_posts_json = request.COOKIES.get(CookieManager.VIEWED_POSTS_COOKIE, '[]')
        
        try:
            viewed_posts = json.loads(viewed_posts_json)
            if not isinstance(viewed_posts, list):
                viewed_posts = []
        except (json.JSONDecodeError, ValueError):
            # Handle malformed cookie data
            viewed_posts = []
        
        return post_id in viewed_posts
    
    @staticmethod
    def mark_post_viewed(response, post_id: int, request=None) -> None:
        """
        Mark a post as viewed by adding it to the viewed posts cookie.
        
        Args:
            response: Django HttpResponse object
            post_id: Blog post ID to mark as viewed
            request: Django HttpRequest object (optional, to read existing viewed posts)
        """
        # Get existing viewed posts from request cookies if available
        viewed_posts = []
        if request is not None:
            viewed_posts_json = request.COOKIES.get(CookieManager.VIEWED_POSTS_COOKIE, '[]')
            try:
                viewed_posts = json.loads(viewed_posts_json)
                if not isinstance(viewed_posts, list):
                    viewed_posts = []
            except (json.JSONDecodeError, ValueError):
                viewed_posts = []
        
        # Add the new post ID
        if post_id not in viewed_posts:
            viewed_posts.append(post_id)
        
        # Store as JSON array
        viewed_posts_json = json.dumps(viewed_posts)
        
        response.set_cookie(
            key=CookieManager.VIEWED_POSTS_COOKIE,
            value=viewed_posts_json,
            max_age=CookieManager.VIEWED_POSTS_MAX_AGE,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    @staticmethod
    def get_visitor_identifier(request) -> str:
        """
        Get unique visitor identifier for rate limiting.
        
        Combines IP address and visitor ID for a unique identifier.
        
        Args:
            request: Django HttpRequest object
        
        Returns:
            str: Unique identifier in format "ip:visitor_id"
        """
        from blog.utils.helpers import get_client_ip
        
        ip = get_client_ip(request)
        visitor_id = CookieManager.get_or_create_visitor_id(request, None)
        
        return f"{ip}:{visitor_id}"
