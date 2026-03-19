from django.db import models
from tinymce.models import HTMLField

class Tags(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    image = models.ImageField(upload_to='category_images/')
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name



class BlogPost(models.Model):
    banner = models.ImageField(upload_to='blog_banners/')
    title = models.CharField(max_length=200)
    content = HTMLField()
    published_date = models.DateTimeField(auto_now_add=True, db_index=True)
    # mark a small set of posts as featured for the home page
    is_featured = models.BooleanField(default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)

    # relation ships
    tags = models.ManyToManyField(Tags, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='blog_posts', db_index=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True, db_index=True)

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        from django.core.cache import cache
        
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base or 'post'
            count = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
                slug = f"{base}-{count}"
                count += 1
            self.slug = slug
        
        super().save(*args, **kwargs)
        
        # Invalidate blog caches when post is created/updated
        cache.delete('blog:filters')

    class Meta:
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', '-published_date']),
            models.Index(fields=['category', '-published_date']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments', db_index=True)
    first_name = models.CharField(max_length=50, default='Anonymous')
    last_name = models.CharField(max_length=50, default='User')
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    visitor_id = models.CharField(max_length=36, db_index=True, default='00000000-0000-0000-0000-000000000000')
    ip_address = models.GenericIPAddressField(db_index=True, default='127.0.0.1')
    user_agent = models.TextField(default='')
    is_approved = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blog_post', '-created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['visitor_id']),
            models.Index(fields=['is_approved', '-created_at']),
        ]

    def __str__(self):
        return f'Comment by {self.first_name} {self.last_name} on {self.blog_post.title}'


class Like(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes', db_index=True)
    visitor_id = models.CharField(max_length=36, db_index=True, default='00000000-0000-0000-0000-000000000000')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('blog_post', 'visitor_id')
        indexes = [
            models.Index(fields=['blog_post', 'visitor_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Like on {self.blog_post.title}'


class Dislike(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='dislikes', db_index=True)
    visitor_id = models.CharField(max_length=36, db_index=True, default='00000000-0000-0000-0000-000000000000')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('blog_post', 'visitor_id')
        indexes = [
            models.Index(fields=['blog_post', 'visitor_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Dislike on {self.blog_post.title}'