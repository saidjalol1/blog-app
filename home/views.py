from django.shortcuts import render
from django.views import View
from django.db.models import Count
from blog.models import BlogPost, Category, Tags


class HomePage(View):
    def get(self, request):
        # Featured and latest posts for server-side rendering + SEO
        featured_posts = BlogPost.objects.select_related('category').prefetch_related('tags').filter(is_featured=True).order_by('-published_date')[:6]
        latest_posts = BlogPost.objects.select_related('category').prefetch_related('tags').order_by('-published_date')[:12]
        categories = Category.objects.annotate(post_count=Count('blog_posts'))[:12]
        context = {
            'featured_posts': featured_posts,
            'latest_posts': latest_posts,
            'categories': categories,
        }
        return render(request, 'index.html', context)

    def post(self, request):
        # Keep POST fallback
        return self.get(request)

    