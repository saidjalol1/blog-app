"""
Production settings for Django blog application.

This module inherits from base settings and overrides configurations
for production deployment with security hardening.
"""

import os
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable must be set in production. "
        "Generate a secure key using: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# ALLOWED_HOSTS must be configured for production
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError(
        "DJANGO_ALLOWED_HOSTS environment variable must be set in production. "
        "Example: DJANGO_ALLOWED_HOSTS=example.com,www.example.com"
    )

# Remove any empty strings from ALLOWED_HOSTS
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# HTTPS and SSL Settings
# Force HTTPS redirect for all requests
SECURE_SSL_REDIRECT = True

# Trust the X-Forwarded-Proto header from proxy (e.g., nginx, load balancer)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTP Strict Transport Security (HSTS) Settings
# Tell browsers to only use HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds

# Apply HSTS to all subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Allow site to be preloaded into browsers' HSTS preload list
SECURE_HSTS_PRELOAD = True

# Security Headers
# Prevent the site from being embedded in iframes (clickjacking protection)
X_FRAME_OPTIONS = 'DENY'

# Prevent browsers from MIME-sniffing content types
SECURE_CONTENT_TYPE_NOSNIFF = True

# Enable browser's XSS filtering
SECURE_BROWSER_XSS_FILTER = True

# Secure Cookie Settings
# Session Cookie Security
SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection, allows top-level navigation

# CSRF Cookie Security
CSRF_COOKIE_SECURE = True  # Only send CSRF cookie over HTTPS
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Lax'  # CSRF protection, allows top-level navigation

# Content Security Policy (CSP) Configuration
# Define CSP directives to prevent XSS and other injection attacks

# Default source - only allow resources from same origin
CSP_DEFAULT_SRC = ("'self'",)

# Script sources - allow scripts from self and specific CDNs
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for some inline scripts (consider removing if possible)
    "cdn.jsdelivr.net",  # CDN for libraries
)

# Style sources - allow styles from self and Google Fonts
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline styles
    "fonts.googleapis.com",
)

# Font sources - allow fonts from self and Google Fonts
CSP_FONT_SRC = (
    "'self'",
    "fonts.gstatic.com",
)

# Image sources - allow images from self, data URIs, and HTTPS sources
CSP_IMG_SRC = (
    "'self'",
    "data:",  # Allow data URIs for inline images
    "https:",  # Allow any HTTPS image source
)

# Connect sources - allow AJAX/WebSocket connections to self
CSP_CONNECT_SRC = ("'self'",)

# Frame sources - disallow embedding any frames
CSP_FRAME_SRC = ("'none'",)

# Object sources - disallow plugins like Flash
CSP_OBJECT_SRC = ("'none'",)

# Base URI - restrict base tag URLs to self
CSP_BASE_URI = ("'self'",)

# Form action - restrict form submissions to self
CSP_FORM_ACTION = ("'self'",)

# Frame ancestors - prevent site from being embedded (redundant with X-Frame-Options)
CSP_FRAME_ANCESTORS = ("'none'",)

# Database Configuration for Production
# Support for PostgreSQL and MySQL with environment-based configuration
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Parse database URL from environment variable
# Format: postgresql://user:password@host:port/dbname
# or: mysql://user:password@host:port/dbname
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Parse database URL
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,  # Persistent connections (10 minutes)
            conn_health_checks=True,  # Enable connection health checks
        )
    }
    
    # Connection pooling configuration
    # Adjust pool size based on your deployment (workers * threads)
    DATABASES['default']['OPTIONS'] = DATABASES['default'].get('OPTIONS', {})
    
    # PostgreSQL-specific settings
    if 'postgresql' in DATABASES['default']['ENGINE']:
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 10,  # Connection timeout in seconds
            'options': '-c statement_timeout=30000',  # Query timeout (30 seconds)
        })
    
    # MySQL-specific settings
    elif 'mysql' in DATABASES['default']['ENGINE']:
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 10,  # Connection timeout in seconds
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        })
else:
    # Fallback to individual environment variables if DATABASE_URL not set
    DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.postgresql')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432' if 'postgresql' in DB_ENGINE else '3306')
    
    if not all([DB_NAME, DB_USER, DB_PASSWORD]):
        raise ValueError(
            "Database configuration required. Set DATABASE_URL or "
            "DB_NAME, DB_USER, and DB_PASSWORD environment variables."
        )
    
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'CONN_MAX_AGE': 600,  # Persistent connections (10 minutes)
            'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
            'OPTIONS': {},
        }
    }
    
    # PostgreSQL-specific settings
    if 'postgresql' in DB_ENGINE:
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        })
    
    # MySQL-specific settings
    elif 'mysql' in DB_ENGINE:
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 10,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        })

# Redis Cache Configuration for Production
# Override base cache settings with production Redis configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
        "KEY_PREFIX": "blog_prod",
        "TIMEOUT": 300,  # Default TTL: 5 minutes
    }
}

# Use Redis for session storage in production
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Static file optimization with WhiteNoise
# WhiteNoise is already configured in base.py middleware
# Add browser caching headers for static assets
WHITENOISE_MAX_AGE = 31536000  # 1 year in seconds for immutable assets
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: True  # All static files are immutable
WHITENOISE_COMPRESS_OFFLINE = True  # Enable static file compression

# Override logging configuration for production
# Enable DEBUG level for django.db.backends to capture slow queries
LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

# Sentry Error Tracking Configuration
# Install sentry-sdk with: pip install sentry-sdk
SENTRY_DSN = os.environ.get('SENTRY_DSN')

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            # In production, you may want to reduce this to save on quota
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            
            # Send error events for these log levels
            event_level='ERROR',
            
            # Set environment name
            environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
            
            # Send default PII (Personally Identifiable Information)
            # Set to False if you want to exclude user IP, cookies, etc.
            send_default_pii=False,
            
            # Attach stack traces to messages
            attach_stacktrace=True,
        )
    except ImportError:
        # Sentry SDK not installed - log warning but don't fail
        import warnings
        warnings.warn(
            "SENTRY_DSN is set but sentry-sdk is not installed. "
            "Install it with: pip install sentry-sdk"
        )
