"""
Context processors for making SEO and site settings available in all templates.
"""

from django.conf import settings


def seo_settings(request):
    """Add SEO-related settings to template context."""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'My Blog'),
        'site_url': getattr(settings, 'SITE_URL', ''),
        'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
        'site_keywords': getattr(settings, 'SITE_KEYWORDS', ''),
        'social_media': getattr(settings, 'SOCIAL_MEDIA', {}),
    }
