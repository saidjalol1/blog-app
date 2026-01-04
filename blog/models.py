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
    published_date = models.DateTimeField(auto_now_add=True)
    # mark a small set of posts as featured for the home page
    is_featured = models.BooleanField(default=False, db_index=True)

    # relation ships
    tags = models.ManyToManyField(Tags, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='blog_posts')
    slug = models.SlugField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base or 'post'
            count = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=getattr(self, 'pk', None)).exists():
                slug = f"{base}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'Comment by {self.author.first_name} {self.author.last_name} on {self.blog_post.title}'