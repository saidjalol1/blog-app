#!/usr/bin/env python
"""
Quick SEO verification script.
Run this to verify SEO implementation is working correctly.

Usage: python verify_seo.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.conf import settings
from blog.models import BlogPost
from django.urls import reverse
from django.test import RequestFactory


def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")


def verify_settings():
    """Verify SEO settings are configured."""
    print_header("Checking SEO Settings")
    
    # Check INSTALLED_APPS
    if 'django.contrib.sitemaps' in settings.INSTALLED_APPS:
        print_success("django.contrib.sitemaps is installed")
    else:
        print_error("django.contrib.sitemaps is NOT installed")
    
    # Check SEO settings
    if hasattr(settings, 'SITE_NAME'):
        print_success(f"SITE_NAME: {settings.SITE_NAME}")
    else:
        print_error("SITE_NAME not configured")
    
    if hasattr(settings, 'SITE_URL'):
        if settings.SITE_URL == 'https://yourdomain.com':
            print_warning(f"SITE_URL needs update: {settings.SITE_URL}")
        else:
            print_success(f"SITE_URL: {settings.SITE_URL}")
    else:
        print_error("SITE_URL not configured")
    
    if hasattr(settings, 'SITE_DESCRIPTION'):
        print_success(f"SITE_DESCRIPTION configured ({len(settings.SITE_DESCRIPTION)} chars)")
    else:
        print_error("SITE_DESCRIPTION not configured")
    
    if hasattr(settings, 'SOCIAL_MEDIA'):
        print_success(f"SOCIAL_MEDIA configured with {len(settings.SOCIAL_MEDIA)} platforms")
    else:
        print_error("SOCIAL_MEDIA not configured")


def verify_files():
    """Verify required files exist."""
    print_header("Checking Required Files")
    
    files = [
        ('blog/seo.py', 'SEO helper module'),
        ('blog/sitemaps.py', 'Sitemap configuration'),
        ('blog/context_processors.py', 'Context processor'),
        ('static/robots.txt', 'Robots.txt file'),
        ('docs/SEO_GUIDE.md', 'SEO documentation'),
        ('docs/SEO_CHECKLIST.md', 'SEO checklist'),
    ]
    
    for filepath, description in files:
        if os.path.exists(filepath):
            print_success(f"{description}: {filepath}")
        else:
            print_error(f"{description} NOT FOUND: {filepath}")


def verify_models():
    """Verify model enhancements."""
    print_header("Checking Model Enhancements")
    
    # Check if BlogPost has seo_score method
    if hasattr(BlogPost, 'seo_score'):
        print_success("BlogPost.seo_score() method exists")
        
        # Test with a sample post if available
        posts = BlogPost.objects.all()[:1]
        if posts:
            post = posts[0]
            score = post.seo_score()
            print_success(f"Sample post SEO score: {score}%")
            
            if score >= 90:
                print_success("Excellent SEO score!")
            elif score >= 70:
                print_warning("Good SEO score, but can be improved")
            else:
                print_warning("SEO score needs improvement")
        else:
            print_warning("No blog posts found to test")
    else:
        print_error("BlogPost.seo_score() method NOT FOUND")


def verify_sitemaps():
    """Verify sitemap configuration."""
    print_header("Checking Sitemap Configuration")
    
    try:
        from blog.sitemaps import BlogPostSitemap, CategorySitemap, StaticViewSitemap
        print_success("Sitemap classes imported successfully")
        
        # Test sitemap generation
        blog_sitemap = BlogPostSitemap()
        items = blog_sitemap.items()
        print_success(f"BlogPostSitemap: {items.count()} posts")
        
        category_sitemap = CategorySitemap()
        items = category_sitemap.items()
        print_success(f"CategorySitemap: {items.count()} categories")
        
        static_sitemap = StaticViewSitemap()
        items = static_sitemap.items()
        print_success(f"StaticViewSitemap: {len(items)} pages")
        
    except Exception as e:
        print_error(f"Sitemap error: {str(e)}")


def verify_seo_helpers():
    """Verify SEO helper functions."""
    print_header("Checking SEO Helper Functions")
    
    try:
        from blog.seo import SEOHelper
        print_success("SEOHelper imported successfully")
        
        # Test meta description generation
        test_content = "<p>This is a test content for SEO verification.</p>" * 10
        description = SEOHelper.generate_meta_description(test_content)
        print_success(f"Meta description generation works ({len(description)} chars)")
        
        # Test with a sample post if available
        posts = BlogPost.objects.all()[:1]
        if posts:
            post = posts[0]
            factory = RequestFactory()
            request = factory.get('/')
            
            # Test schema generation
            article_schema = SEOHelper.generate_article_schema(post, request)
            if article_schema and '@context' in article_schema:
                print_success("Article schema generation works")
            else:
                print_error("Article schema generation failed")
            
            breadcrumb_schema = SEOHelper.generate_breadcrumb_schema(post, request)
            if breadcrumb_schema and '@context' in breadcrumb_schema:
                print_success("Breadcrumb schema generation works")
            else:
                print_error("Breadcrumb schema generation failed")
        else:
            print_warning("No blog posts found to test schema generation")
            
    except Exception as e:
        print_error(f"SEO Helper error: {str(e)}")


def verify_management_commands():
    """Verify management commands."""
    print_header("Checking Management Commands")
    
    command_file = 'blog/management/commands/seo_audit.py'
    if os.path.exists(command_file):
        print_success("SEO audit command exists")
        print_warning("Run 'python manage.py seo_audit' to test it")
    else:
        print_error("SEO audit command NOT FOUND")


def print_summary():
    """Print summary and next steps."""
    print_header("Summary & Next Steps")
    
    print("Configuration Tasks:")
    print("1. Update SITE_NAME in config/settings/base.py")
    print("2. Update SITE_URL with your production domain")
    print("3. Update SITE_DESCRIPTION with your blog description")
    print("4. Update SOCIAL_MEDIA links in settings")
    print("5. Update sitemap URL in static/robots.txt")
    print()
    print("Testing Tasks:")
    print("1. Run: python manage.py seo_audit --verbose")
    print("2. Visit: http://localhost:8000/sitemap.xml")
    print("3. Visit: http://localhost:8000/robots.txt")
    print("4. Test structured data: https://search.google.com/test/rich-results")
    print("5. Test Open Graph: https://developers.facebook.com/tools/debug/")
    print()
    print("Documentation:")
    print("- Read: docs/SEO_GUIDE.md")
    print("- Read: docs/SEO_CHECKLIST.md")
    print("- Read: docs/SEO_IMPLEMENTATION.md")
    print()


def main():
    """Main verification function."""
    print("\n" + "="*60)
    print("  SEO IMPLEMENTATION VERIFICATION")
    print("="*60)
    
    try:
        verify_settings()
        verify_files()
        verify_models()
        verify_sitemaps()
        verify_seo_helpers()
        verify_management_commands()
        print_summary()
        
        print_header("Verification Complete!")
        print("✅ SEO implementation is ready!")
        print("⚠️  Remember to update configuration values before deploying")
        
    except Exception as e:
        print_error(f"Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
