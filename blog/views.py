from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage
from django.utils.text import slugify
from django.utils.html import strip_tags

from .models import BlogPost, Category


def blog_page(request):
    # Server-render the first page for SEO and client fallback and respect URL filters
    POSTS_PER_PAGE = 5
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    q = request.GET.get('q', '').strip()
    categories = [c for c in request.GET.get('categories', '').split(',') if c]
    tags = [t for t in request.GET.get('tags', '').split(',') if t]
    sort = request.GET.get('sort', 'new')

    qs = BlogPost.objects.select_related('category').prefetch_related('tags')

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
        qs = qs.order_by('-comments__count', '-published_date')
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
            'views': p.comments.count(),
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
@cache_page(120)
def fetch_blogs(request):
    """API endpoint for paginated, filterable blog posts.

    Accepts GET params:
      - page: int (default 1)
      - per_page: int (default 10, max 50)
      - q: search query (title or content)
      - categories: comma-separated category names
      - tags: comma-separated tag names
      - sort: 'new'|'old'|'popular' (default 'new')

    Returns JSON: { results: [...], page, per_page, total, total_pages }
    """
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(int(request.GET.get('per_page', 10)), 50)
    except (TypeError, ValueError):
        per_page = 10

    q = request.GET.get('q', '').strip()
    categories = [c for c in request.GET.get('categories', '').split(',') if c]
    tags = [t for t in request.GET.get('tags', '').split(',') if t]
    sort = request.GET.get('sort', 'new')

    qs = BlogPost.objects.select_related('category').prefetch_related('tags').annotate(comment_count=Count('comments'))

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
@cache_page(120)
def fetch_filters(request):
    """Return categories and tags with counts for building filter lists in the UI."""
    from django.db.models import Count
    categories = Category.objects.annotate(post_count=Count('blog_posts')).values('name', 'post_count')

    from .models import Tags
    tags = Tags.objects.annotate(post_count=Count('blog_posts')).values('name', 'post_count')

    payload = {
        'categories': list(categories),
        'tags': list(tags),
    }
    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})


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


def blog_post_detail(request, slug):
    """Server-rendered blog detail page (slug-based)."""
    from django.shortcuts import get_object_or_404
    post = get_object_or_404(BlogPost.objects.select_related('category').prefetch_related('tags', 'comments__author'), slug=slug)

    comments = post.comments.select_related('author').order_by('-created_at')[:50]

    meta_description = strip_tags(post.content)[:160]
    meta_image = request.build_absolute_uri(post.banner.url) if post.banner and hasattr(post.banner, 'url') else ''
    canonical = request.build_absolute_uri()

    context = {
        'post': post,
        'comments': comments,
        'meta_description': meta_description,
        'meta_image': meta_image,
        'canonical': canonical,
    }
    return render(request, 'blog-detail.html', context)

