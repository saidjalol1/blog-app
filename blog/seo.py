"""
SEO utilities for blog application.
Provides structured data, meta tags, and SEO optimization helpers.
"""

from django.utils.html import strip_tags
from django.utils.text import Truncator
from urllib.parse import urljoin


class SEOHelper:
    """Helper class for generating SEO-optimized meta tags and structured data."""
    
    @staticmethod
    def generate_meta_description(content, max_length=160):
        """Generate SEO-friendly meta description from content."""
        text = strip_tags(content)
        truncator = Truncator(text)
        return truncator.chars(max_length, truncate='...')
    
    @staticmethod
    def generate_article_schema(post, request):
        """Generate JSON-LD structured data for article."""
        from django.conf import settings
        
        site_name = getattr(settings, 'SITE_NAME', 'My Blog')
        site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/'))
        
        image_url = None
        if post.banner and hasattr(post.banner, 'url'):
            image_url = request.build_absolute_uri(post.banner.url)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": SEOHelper.generate_meta_description(post.content),
            "image": image_url,
            "datePublished": post.published_date.isoformat(),
            "dateModified": post.published_date.isoformat(),
            "author": {
                "@type": "Organization",
                "name": site_name,
                "url": site_url
            },
            "publisher": {
                "@type": "Organization",
                "name": site_name,
                "url": site_url,
                "logo": {
                    "@type": "ImageObject",
                    "url": request.build_absolute_uri('/static/blog.png')
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": request.build_absolute_uri()
            },
            "articleSection": post.category.name if post.category else None,
            "keywords": ", ".join([tag.name for tag in post.tags.all()]),
            "wordCount": len(strip_tags(post.content).split()),
            "commentCount": post.comments.filter(is_approved=True).count(),
            "interactionStatistic": [
                {
                    "@type": "InteractionCounter",
                    "interactionType": "https://schema.org/LikeAction",
                    "userInteractionCount": post.likes.count()
                },
                {
                    "@type": "InteractionCounter",
                    "interactionType": "https://schema.org/DislikeAction",
                    "userInteractionCount": post.dislikes.count()
                }
            ]
        }
        
        return schema
    
    @staticmethod
    def generate_breadcrumb_schema(post, request):
        """Generate JSON-LD breadcrumb structured data."""
        from django.urls import reverse
        
        items = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": request.build_absolute_uri('/')
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Blog",
                "item": request.build_absolute_uri(reverse('blog:blog_page'))
            }
        ]
        
        if post.category:
            items.append({
                "@type": "ListItem",
                "position": 3,
                "name": post.category.name,
                "item": request.build_absolute_uri(reverse('blog:blog_page') + f'?categories={post.category.name}')
            })
            items.append({
                "@type": "ListItem",
                "position": 4,
                "name": post.title,
                "item": request.build_absolute_uri()
            })
        else:
            items.append({
                "@type": "ListItem",
                "position": 3,
                "name": post.title,
                "item": request.build_absolute_uri()
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items
        }
    
    @staticmethod
    def generate_website_schema(request):
        """Generate JSON-LD structured data for website."""
        from django.conf import settings
        from django.urls import reverse
        
        site_name = getattr(settings, 'SITE_NAME', 'My Blog')
        site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/'))
        
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site_name,
            "url": site_url,
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": site_url + "blogs/?q={search_term_string}"
                },
                "query-input": "required name=search_term_string"
            }
        }
    
    @staticmethod
    def generate_organization_schema(request):
        """Generate JSON-LD structured data for organization."""
        from django.conf import settings
        
        site_name = getattr(settings, 'SITE_NAME', 'My Blog')
        site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/'))
        
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": site_name,
            "url": site_url,
            "logo": request.build_absolute_uri('/static/blog.png'),
            "sameAs": [
                # Add your social media profiles here
            ]
        }
