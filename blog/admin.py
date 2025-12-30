from django.contrib import admin
from .models import Tags, Category, BlogPost, Comment
from .forms import BlogPostAdminForm


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    list_display = ('title', 'published_date', 'category')
    list_filter = ('published_date', 'category', 'tags')
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'blog_post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content')
    raw_id_fields = ('author', 'blog_post')
