from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from blog.sitemaps import BlogPostSitemap, CategorySitemap, StaticViewSitemap

# Sitemap configuration
sitemaps = {
    'blog_posts': BlogPostSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: https://gayratxoldarov.uz/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls', namespace='home')),
    path('blogs/', include('blog.urls', namespace='blog')),
    path('about/', include('about.urls', namespace='about')),
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt),  # ← fixed
    # Tools
    path('tinymce/', include('tinymce.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)