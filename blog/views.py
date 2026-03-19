from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import cache_page
from django.db.models import Count, Q
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.core.cache import cache
from django.conf import settings

from .models import BlogPost, Category
from blog.utils.cookie_manager import CookieManager
from blog.utils.rate_limiter import rate_limit
from blog.utils.helpers import get_client_ip, sanitize_comment_content


# Cache invalidation helper
def invalidate_blog_caches():
    """Invalidate all blog-related caches when posts are created/updated."""
    cache.delete('blog:filters')
    # Clear cache_page caches by deleting the cache keys
    # Note: cache_page uses a complex key structure, so we rely on TTL expiration


@cache_page(300)  # Cache for 5 minutes
def blog_page(request):
    # Server-render the first page for SEO and client fallback and respect URL filters
    POSTS_PER_PAGE = getattr(settings, 'BLOG_POSTS_PER_PAGE', 50)
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    q = request.GET.get('q', '').strip()
    categories = [c for c in request.GET.get('categories', '').split(',') if c]
    tags = [t for t in request.GET.get('tags', '').split(',') if t]
    sort = request.GET.get('sort', 'new')

    # Query optimization: select_related for foreign keys, prefetch_related for many-to-many
    # annotate for counts to avoid N+1 queries
    qs = BlogPost.objects.select_related('category').prefetch_related('tags', 'comments').annotate(
        like_count=Count('likes', distinct=True),
        dislike_count=Count('dislikes', distinct=True),
        comment_count=Count('comments', distinct=True)
    )

    if categories:
        qs = qs.filter(category__name__in=categories)
    if tags:
        qs = qs.filter(tags__name__in=tags)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    qs = qs.distinct()

    if sort == 'old':
        qs = qs.order_by('published_date')
    elif sort == 'popular':
        qs = qs.order_by('-comment_count', '-published_date')
    else:
        qs = qs.order_by('-published_date')

    paginator = Paginator(qs, POSTS_PER_PAGE)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    def short_post(p):
        excerpt = strip_tags(p.content)[:240].strip()
        if len(excerpt) == 240:
            excerpt = excerpt.rsplit(' ', 1)[0] + '…'
        return {
            'id': p.id,
            'slug': p.slug,
            'title': p.title,
            'excerpt': excerpt,
            'content': strip_tags(p.content),
            'img': request.build_absolute_uri(p.banner.url) if p.banner and hasattr(p.banner, 'url') else '',
            'date': p.published_date.isoformat(),
            'views': getattr(p, 'comment_count', 0),
            'tags': [t.name for t in p.tags.all()],
            'category': p.category.name if p.category else None,
        }

    initial_posts = [short_post(p) for p in page_obj.object_list]

    initial_filters = {'categories': categories, 'tags': tags, 'q': q, 'sort': sort}

    context = {
        'initial_posts': initial_posts,
        'page': page_obj.number,
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'selected_categories': categories,
        'selected_tags': tags,
        'search_query': q,
        'sort': sort,
        'initial_filters': initial_filters,
    }
    return render(request, 'blog.html', context)


@require_GET
def fetch_blogs(request):
    """API endpoint for paginated, filterable blog posts.

    Accepts GET params:
      - page: int (default 1)
      - per_page: int (default 50, max 50)
      - q: search query (title or content)
      - categories: comma-separated category names
      - tags: comma-separated tag names
      - sort: 'new'|'old'|'popular' (default 'new')

    Returns JSON: { results: [...], page, per_page, total, total_pages }
    """
    max_per_page = getattr(settings, 'BLOG_POSTS_PER_PAGE', 50)
    
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(int(request.GET.get('per_page', max_per_page)), max_per_page)
    except (TypeError, ValueError):
        per_page = max_per_page

    q = request.GET.get('q', '').strip()
    categories = [c for c in request.GET.get('categories', '').split(',') if c]
    tags = [t for t in request.GET.get('tags', '').split(',') if t]
    sort = request.GET.get('sort', 'new')

    # Query optimization: select_related for foreign keys, prefetch_related for many-to-many
    # annotate for counts to avoid N+1 queries
    qs = BlogPost.objects.select_related('category').prefetch_related('tags', 'comments').annotate(
        like_count=Count('likes', distinct=True),
        dislike_count=Count('dislikes', distinct=True),
        comment_count=Count('comments', distinct=True)
    )

    # Filters
    if categories:
        qs = qs.filter(category__name__in=categories)
    if tags:
        qs = qs.filter(tags__name__in=tags)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    qs = qs.distinct()

    if sort == 'old':
        qs = qs.order_by('published_date')
    elif sort == 'popular':
        qs = qs.order_by('-comment_count', '-published_date')
    else:
        qs = qs.order_by('-published_date')


    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    def post_to_dict(post):
        excerpt = strip_tags(post.content)[:240].strip()
        if len(excerpt) == 240:
            excerpt = excerpt.rsplit(' ', 1)[0] + '…'
        image_url = request.build_absolute_uri(post.banner.url) if post.banner and hasattr(post.banner, 'url') else ''
        return {
            'id': post.id,
            'slug': post.slug,
            'title': post.title,
            'excerpt': excerpt,
            'content': strip_tags(post.content),
            'img': image_url,
            'date': post.published_date.isoformat(),
            'views': getattr(post, 'comment_count', 0),  
            'tags': [t.name for t in post.tags.all()],
            'category': post.category.name if post.category else None,
        }

    results = [post_to_dict(p) for p in page_obj.object_list]

    payload = {
        'results': results,
        'page': page_obj.number,
        'per_page': per_page,
        'total': paginator.count,
        'total_pages': paginator.num_pages,
    }
    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})


@require_GET
def fetch_filters(request):
    """Return categories and tags with counts for building filter lists in the UI.
    Cached for 15 minutes."""
    cache_key = 'blog:filters'
    filters = cache.get(cache_key)
    
    if filters is None:
        from django.db.models import Count
        categories = Category.objects.annotate(post_count=Count('blog_posts')).values('name', 'post_count')

        from .models import Tags
        tags = Tags.objects.annotate(post_count=Count('blog_posts')).values('name', 'post_count')

        filters = {
            'categories': list(categories),
            'tags': list(tags),
        }
        
        # Cache for 15 minutes (900 seconds)
        cache.set(cache_key, filters, 900)
    
    return JsonResponse(filters, json_dumps_params={'ensure_ascii': False})


@require_GET
def blog_post_json(request, slug):
    """Return JSON for a single blog post (used by AJAX fallback). Look up by slug."""
    try:
        post = BlogPost.objects.select_related('category').prefetch_related('tags').get(slug=slug)
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    from django.db.models import Count
    views_count = post.comments.count()
    desc = strip_tags(post.content)[:160]
    data = {
        'id': post.id,
        'slug': post.slug,
        'title': post.title,
        'content_html': post.content,
        'excerpt': strip_tags(post.content)[:240],
        'description': desc,
        'img': request.build_absolute_uri(post.banner.url) if post.banner and hasattr(post.banner, 'url') else '',
        'date': post.published_date.isoformat(),
        'tags': [t.name for t in post.tags.all()],
        'category': post.category.name if post.category else None,
        'views': views_count,
        'author': '',
        'avatar': '',
        'read': '',
        'canonical': request.build_absolute_uri(),
    }
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


@rate_limit('comment', limit=3, window=600)
def blog_post_detail(request, slug):
    """Server-rendered blog detail page (slug-based)."""
    from django.db.models import F
    from django.shortcuts import redirect
    from .forms import CommentForm
    from .utils.helpers import sanitize_comment_content
    import logging
    
    logger = logging.getLogger('blog')
    
    post = get_object_or_404(BlogPost.objects.select_related('category').prefetch_related('tags', 'comments'), slug=slug)

    if request.method == 'POST':
        # Use CommentForm for validation
        form = CommentForm(request.POST)
        
        if form.is_valid():
            # Extract IP address and user agent
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Get or create visitor_id from cookie
            response = HttpResponse()  # Temporary response for cookie setting
            visitor_id = CookieManager.get_or_create_visitor_id(request, response)
            
            # Sanitize comment content before saving
            sanitized_content = sanitize_comment_content(form.cleaned_data['content'])
            
            # Create comment with all metadata - wrapped in transaction
            with transaction.atomic():
                comment = form.save(commit=False)
                comment.blog_post = post
                comment.content = sanitized_content
                comment.ip_address = ip_address
                comment.user_agent = user_agent
                comment.visitor_id = visitor_id
                comment.save()
            
            # Log comment submission
            logger.info(f"Comment submitted on post {slug} from IP {ip_address} at {comment.created_at}")
            
            return redirect('blog:blog_post_detail', slug=slug)
        else:
            # Form validation failed - re-render with errors
            comments = post.comments.order_by('-created_at')[:50]
            visitor_id = CookieManager.get_or_create_visitor_id(request, None)
            user_liked = post.likes.filter(visitor_id=visitor_id).exists()
            user_disliked = post.dislikes.filter(visitor_id=visitor_id).exists()
            
            context = {
                'post': post,
                'comments': comments,
                'form': form,
                'user_liked': user_liked,
                'user_disliked': user_disliked,
                'likes_count': post.likes.count(),
                'dislikes_count': post.dislikes.count(),
            }
            return render(request, 'blog-detail.html', context)

    # GET request - display form and comments
    form = CommentForm()
    comments = post.comments.order_by('-created_at')[:50]

    # Check if user liked/disliked using visitor_id
    visitor_id = CookieManager.get_or_create_visitor_id(request, None)
    user_liked = post.likes.filter(visitor_id=visitor_id).exists()
    user_disliked = post.dislikes.filter(visitor_id=visitor_id).exists()

    meta_description = strip_tags(post.content)[:160]
    meta_image = request.build_absolute_uri(post.banner.url) if post.banner and hasattr(post.banner, 'url') else ''
    canonical = request.build_absolute_uri()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'meta_description': meta_description,
        'meta_image': meta_image,
        'canonical': canonical,
        'user_liked': user_liked,
        'user_disliked': user_disliked,
        'likes_count': post.likes.count(),
        'dislikes_count': post.dislikes.count(),
    }
    
    response = render(request, 'blog-detail.html', context)
    
    # Increment view count if visitor hasn't viewed this post before
    if not CookieManager.has_viewed_post(request, post.id):
        # Use F() expression for atomic increment
        BlogPost.objects.filter(pk=post.pk).update(view_count=F('view_count') + 1)
        # Mark post as viewed in cookie
        CookieManager.mark_post_viewed(response, post.id, request)
    
    return response


@require_POST
@rate_limit('like', limit=10, window=60)
@transaction.atomic
def like_post(request, slug):
    """
    Toggle like on a blog post.
    
    POST endpoint at /blog/post/<slug>/like/
    - Gets or creates visitor_id from cookie
    - Removes existing dislike if present
    - Toggles like (create if doesn't exist, delete if exists)
    - Returns JSON with action, likes count, and dislikes count
    - Rate limited to 10 actions per minute
    """
    from .models import Like, Dislike
    
    post = get_object_or_404(BlogPost, slug=slug)
    
    # Get or create visitor_id from cookie
    response = JsonResponse({})  # Temporary response for cookie setting
    visitor_id = CookieManager.get_or_create_visitor_id(request, response)
    
    # Remove existing dislike if present
    Dislike.objects.filter(blog_post=post, visitor_id=visitor_id).delete()
    
    # Toggle like
    like, created = Like.objects.get_or_create(
        blog_post=post,
        visitor_id=visitor_id
    )
    
    if not created:
        # Like already exists, remove it (toggle off)
        like.delete()
        action = 'removed'
    else:
        # Like was created (toggle on)
        action = 'added'
    
    # Get updated counts
    likes_count = post.likes.count()
    dislikes_count = post.dislikes.count()
    
    # Return JSON response
    response = JsonResponse({
        'action': action,
        'likes': likes_count,
        'dislikes': dislikes_count
    })
    
    # Set visitor_id cookie if it was newly created
    if CookieManager.VISITOR_ID_COOKIE not in request.COOKIES:
        response.set_cookie(
            key=CookieManager.VISITOR_ID_COOKIE,
            value=visitor_id,
            max_age=CookieManager.VISITOR_ID_MAX_AGE,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    return response


@require_POST
@rate_limit('dislike', limit=10, window=60)
@transaction.atomic
def dislike_post(request, slug):
    """
    Toggle dislike on a blog post.
    
    POST endpoint at /blog/post/<slug>/dislike/
    - Gets or creates visitor_id from cookie
    - Removes existing like if present
    - Toggles dislike (create if doesn't exist, delete if exists)
    - Returns JSON with action, likes count, and dislikes count
    - Rate limited to 10 actions per minute
    """
    from .models import Like, Dislike
    
    post = get_object_or_404(BlogPost, slug=slug)
    
    # Get or create visitor_id from cookie
    response = JsonResponse({})  # Temporary response for cookie setting
    visitor_id = CookieManager.get_or_create_visitor_id(request, response)
    
    # Remove existing like if present
    Like.objects.filter(blog_post=post, visitor_id=visitor_id).delete()
    
    # Toggle dislike
    dislike, created = Dislike.objects.get_or_create(
        blog_post=post,
        visitor_id=visitor_id
    )
    
    if not created:
        # Dislike already exists, remove it (toggle off)
        dislike.delete()
        action = 'removed'
    else:
        # Dislike was created (toggle on)
        action = 'added'
    
    # Get updated counts
    likes_count = post.likes.count()
    dislikes_count = post.dislikes.count()
    
    # Return JSON response
    response = JsonResponse({
        'action': action,
        'likes': likes_count,
        'dislikes': dislikes_count
    })
    
    # Set visitor_id cookie if it was newly created
    if CookieManager.VISITOR_ID_COOKIE not in request.COOKIES:
        response.set_cookie(
            key=CookieManager.VISITOR_ID_COOKIE,
            value=visitor_id,
            max_age=CookieManager.VISITOR_ID_MAX_AGE,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    return response

