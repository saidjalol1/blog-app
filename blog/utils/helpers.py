"""
Helper utility functions for the blog application.

This module provides common utility functions for:
- IP address extraction
- Content sanitization
- Security helpers
"""

import bleach


def get_client_ip(request) -> str:
    """
    Extract client IP address from request, handling proxy headers.
    
    Checks X-Forwarded-For header first (for proxied requests),
    then falls back to REMOTE_ADDR.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        str: Client IP address
    """
    # Check X-Forwarded-For header (used by proxies/load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # The first IP is the original client
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Fall back to direct connection IP
        ip = request.META.get('REMOTE_ADDR', '')
    
    return ip


def sanitize_comment_content(content: str) -> str:
    """
    Sanitize comment content to prevent XSS attacks.
    
    Removes all HTML tags and JavaScript code from user input.
    
    Args:
        content: Raw comment content from user
    
    Returns:
        str: Sanitized content safe for display
    """
    # No HTML tags allowed in comments - strip everything
    allowed_tags = []
    
    # Clean the content, removing all HTML tags
    sanitized = bleach.clean(content, tags=allowed_tags, strip=True)
    
    return sanitized


def is_suspicious_user_agent(user_agent: str) -> bool:
    """
    Detect suspicious user agents (bots, scrapers, etc.).
    
    Checks for common bot patterns, scrapers, and suspicious clients
    that should be rate-limited more aggressively.
    
    Args:
        user_agent: User agent string from HTTP headers
    
    Returns:
        bool: True if user agent is suspicious, False otherwise
    """
    if not user_agent:
        # Empty user agent is suspicious
        return True
    
    # Convert to lowercase for case-insensitive matching
    ua_lower = user_agent.lower()
    
    # Common bot and scraper patterns
    suspicious_patterns = [
        'bot',           # Generic bots
        'crawler',       # Web crawlers
        'spider',        # Web spiders
        'scraper',       # Scrapers
        'scrapy',        # Scrapy framework
        'curl',          # Command-line tool
        'wget',          # Command-line tool
        'python-requests',  # Python requests library
        'http',          # Generic HTTP clients (httpie, etc.)
        'java/',         # Java HTTP clients
        'go-http-client',  # Go HTTP clients
        'axios',         # JavaScript HTTP client (when used server-side)
        'postman',       # API testing tool
        'insomnia',      # API testing tool
        'scanner',       # Security scanners
        'nikto',         # Security scanner
        'nmap',          # Network scanner
        'masscan',       # Port scanner
        'sqlmap',        # SQL injection tool
        'nessus',        # Vulnerability scanner
        'openvas',       # Vulnerability scanner
        'metasploit',    # Penetration testing framework
        'havij',         # SQL injection tool
        'acunetix',      # Web vulnerability scanner
        'netsparker',    # Web security scanner
        'appscan',       # Security testing tool
        'burp',          # Security testing tool
        'zap',           # OWASP ZAP security tool
        'qualys',        # Security scanner
        'tenable',       # Security scanner
    ]
    
    # Check if any suspicious pattern is in the user agent
    for pattern in suspicious_patterns:
        if pattern in ua_lower:
            return True
    
    return False
