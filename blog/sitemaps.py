"""
Sitemap configuration for SEO optimization.
Generates XML sitemaps for search engine crawlers.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, Category


class BlogPostSitemap(Sitemap):
    """Sitemap for blog posts."""
    changefreq = "weekly"
    priority = 0.9
    protocol = 'https'
    
    def items(self):
        return BlogPost.objects.all().order_by('-published_date')
    
    def lastmod(self, obj):
        return obj.published_date
    
    def location(self, obj):
        return reverse('blog:blog_post_detail', kwargs={'slug': obj.slug})


class CategorySitemap(Sitemap):
    """Sitemap for category pages."""
    changefreq = "daily"
    priority = 0.7
    protocol = 'https'
    
    def items(self):
        return Category.objects.all()
    
    def location(self, obj):
        return reverse('blog:blog_page') + f'?categories={obj.name}'


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.8
    changefreq = 'monthly'
    protocol = 'https'
    
    def items(self):
        return ['home:home_page', 'blog:blog_page', 'about:about_page']
    
    def location(self, item):
        return reverse(item)
