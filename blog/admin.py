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
    list_display = ('title', 'published_date', 'category', 'view_count', 'seo_health')
    list_filter = ('published_date', 'category', 'tags', 'is_featured')
    search_fields = ('title', 'content', 'slug')
    filter_horizontal = ('tags',)
    readonly_fields = ('slug', 'view_count', 'seo_health_detail')
    
    def seo_health(self, obj):
        """Display SEO score with color coding."""
        score = obj.seo_score()
        if score >= 90:
            color = 'green'
            icon = '✅'
        elif score >= 70:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'red'
            icon = '❌'
        return f'<span style="color: {color}; font-weight: bold;">{icon} {score}%</span>'
    
    seo_health.short_description = 'SEO Score'
    seo_health.allow_tags = True
    
    def seo_health_detail(self, obj):
        """Display detailed SEO analysis."""
        from django.utils.html import strip_tags, format_html
        
        score = obj.seo_score()
        issues = []
        
        # Title check
        if len(obj.title) > 60:
            issues.append('❌ Title too long (> 60 chars)')
        elif len(obj.title) < 30:
            issues.append('⚠️ Title too short (< 30 chars)')
        else:
            issues.append('✅ Title length optimal')
        
        # Category check
        if obj.category:
            issues.append('✅ Category assigned')
        else:
            issues.append('❌ No category assigned')
        
        # Tags check
        tag_count = obj.tags.count()
        if tag_count >= 3:
            issues.append(f'✅ {tag_count} tags assigned')
        elif tag_count > 0:
            issues.append(f'⚠️ Only {tag_count} tags (recommend 3-5)')
        else:
            issues.append('❌ No tags assigned')
        
        # Content length check
        word_count = len(strip_tags(obj.content).split())
        if word_count >= 500:
            issues.append(f'✅ {word_count} words (excellent)')
        elif word_count >= 300:
            issues.append(f'⚠️ {word_count} words (acceptable)')
        else:
            issues.append(f'❌ {word_count} words (too short, need 300+)')
        
        # Banner check
        if obj.banner:
            issues.append('✅ Banner image added')
        else:
            issues.append('❌ No banner image')
        
        # Slug check
        if obj.slug and len(obj.slug) >= 3:
            issues.append(f'✅ Slug: {obj.slug}')
        else:
            issues.append('❌ Slug issue')
        
        html = f'<div style="line-height: 1.8;"><strong>SEO Score: {score}%</strong><br><br>'
        html += '<br>'.join(issues)
        html += '</div>'
        
        return format_html(html)
    
    seo_health_detail.short_description = 'SEO Analysis'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'blog_post', 'created_at', 'is_approved')
    list_filter = ('created_at', 'is_approved')
    search_fields = ('first_name', 'last_name', 'content', 'visitor_id', 'ip_address')
    raw_id_fields = ('blog_post',)
    list_editable = ('is_approved',)
