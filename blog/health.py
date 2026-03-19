"""
Health check endpoint for monitoring system health.

This module provides a health check endpoint that verifies:
- Database connectivity
- Cache (Redis) connectivity
- Overall system status
"""

import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

logger = logging.getLogger('blog')


@require_GET
@never_cache
def health_check(request):
    """
    Health check endpoint that verifies system component health.
    
    Returns JSON with:
    - status: 'healthy' or 'unhealthy'
    - components: dict with status of each component (database, cache)
    - timestamp: current server time
    
    HTTP Status Codes:
    - 200: All components healthy
    - 503: One or more components unhealthy
    """
    components = {}
    overall_healthy = True
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        components['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        components['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_healthy = False
        logger.error(f"Health check: Database connection failed: {str(e)}")
    
    # Check cache (Redis) connectivity
    try:
        # Try to set and get a test value
        test_key = 'health_check_test'
        test_value = 'ok'
        cache.set(test_key, test_value, 10)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            components['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
            # Clean up test key
            cache.delete(test_key)
        else:
            components['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache read/write verification failed'
            }
            overall_healthy = False
            logger.error("Health check: Cache read/write verification failed")
    except Exception as e:
        components['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache connection failed: {str(e)}'
        }
        overall_healthy = False
        logger.error(f"Health check: Cache connection failed: {str(e)}")
    
    # Build response
    from datetime import datetime
    response_data = {
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'components': components,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    status_code = 200 if overall_healthy else 503
    
    return JsonResponse(response_data, status=status_code)
