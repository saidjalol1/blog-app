"""
Unit tests for health check endpoint.
"""

from django.test import TestCase, Client, override_settings
import json


@override_settings(
    ALLOWED_HOSTS=['testserver'],
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class HealthCheckTests(TestCase):
    """Tests for the health check endpoint."""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_check_endpoint_exists(self):
        """Test that the health check endpoint is accessible."""
        response = self.client.get('/blogs/health/')
        self.assertIn(response.status_code, [200, 503],
                     "Health check endpoint should return 200 or 503")
    
    def test_health_check_returns_json(self):
        """Test that the health check endpoint returns JSON."""
        response = self.client.get('/blogs/health/')
        self.assertEqual(response['Content-Type'], 'application/json',
                        "Health check should return JSON")
        
        # Verify JSON is parseable
        data = json.loads(response.content)
        self.assertIsInstance(data, dict,
                            "Health check should return a JSON object")
    
    def test_health_check_has_required_fields(self):
        """Test that the health check response has required fields."""
        response = self.client.get('/blogs/health/')
        data = json.loads(response.content)
        
        # Verify required fields
        self.assertIn('status', data,
                     "Health check should include 'status' field")
        self.assertIn('components', data,
                     "Health check should include 'components' field")
        self.assertIn('timestamp', data,
                     "Health check should include 'timestamp' field")
        
        # Verify status is valid
        self.assertIn(data['status'], ['healthy', 'unhealthy'],
                     "Status should be 'healthy' or 'unhealthy'")
    
    def test_health_check_includes_database_status(self):
        """Test that the health check includes database status."""
        response = self.client.get('/blogs/health/')
        data = json.loads(response.content)
        
        # Verify database component exists
        self.assertIn('database', data['components'],
                     "Health check should include database component")
        
        db_status = data['components']['database']
        self.assertIn('status', db_status,
                     "Database component should have 'status' field")
        self.assertIn('message', db_status,
                     "Database component should have 'message' field")
    
    def test_health_check_includes_cache_status(self):
        """Test that the health check includes cache status."""
        response = self.client.get('/blogs/health/')
        data = json.loads(response.content)
        
        # Verify cache component exists
        self.assertIn('cache', data['components'],
                     "Health check should include cache component")
        
        cache_status = data['components']['cache']
        self.assertIn('status', cache_status,
                     "Cache component should have 'status' field")
        self.assertIn('message', cache_status,
                     "Cache component should have 'message' field")
    
    def test_health_check_returns_200_when_healthy(self):
        """Test that health check returns 200 when all components are healthy."""
        response = self.client.get('/blogs/health/')
        data = json.loads(response.content)
        
        # If all components are healthy, status code should be 200
        if data['status'] == 'healthy':
            self.assertEqual(response.status_code, 200,
                           "Health check should return 200 when healthy")
            
            # Verify all components are healthy
            for component_name, component_status in data['components'].items():
                self.assertEqual(component_status['status'], 'healthy',
                               f"Component {component_name} should be healthy")
    
    def test_health_check_not_cached(self):
        """Test that health check responses are not cached."""
        response1 = self.client.get('/blogs/health/')
        response2 = self.client.get('/blogs/health/')
        
        # Both requests should succeed
        self.assertIn(response1.status_code, [200, 503])
        self.assertIn(response2.status_code, [200, 503])
        
        # Verify Cache-Control header prevents caching
        if 'Cache-Control' in response1:
            cache_control = response1['Cache-Control']
            # Should have no-cache or similar directive
            self.assertTrue(
                'no-cache' in cache_control or 'no-store' in cache_control or 'max-age=0' in cache_control,
                "Health check should not be cached"
            )
