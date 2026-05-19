"""
Management command to audit SEO health of blog posts.
Usage: python manage.py seo_audit
"""

from django.core.management.base import BaseCommand
from django.utils.html import strip_tags
from blog.models import BlogPost


class Command(BaseCommand):
    help = 'Audit SEO health of blog posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each post',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        posts = BlogPost.objects.all()
        
        self.stdout.write(self.style.SUCCESS(f'\n=== SEO Audit Report ==='))
        self.stdout.write(f'Total posts: {posts.count()}\n')
        
        issues = {
            'title_too_long': [],
            'title_too_short': [],
            'no_category': [],
            'no_tags': [],
            'few_tags': [],
            'content_too_short': [],
            'no_banner': [],
            'slug_issues': [],
        }
        
        for post in posts:
            # Title length check (optimal: 50-60 chars)
            if len(post.title) > 60:
                issues['title_too_long'].append(post)
            elif len(post.title) < 30:
                issues['title_too_short'].append(post)
            
            # Category check
            if not post.category:
                issues['no_category'].append(post)
            
            # Tags check
            tag_count = post.tags.count()
            if tag_count == 0:
                issues['no_tags'].append(post)
            elif tag_count < 3:
                issues['few_tags'].append(post)
            
            # Content length check (minimum 300 words)
            content_text = strip_tags(post.content)
            word_count = len(content_text.split())
            if word_count < 300:
                issues['content_too_short'].append(post)
            
            # Banner image check
            if not post.banner:
                issues['no_banner'].append(post)
            
            # Slug check
            if not post.slug or len(post.slug) < 3:
                issues['slug_issues'].append(post)
        
        # Report issues
        self.stdout.write(self.style.WARNING('\n--- Issues Found ---\n'))
        
        if issues['title_too_long']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["title_too_long"])} posts with titles > 60 characters'
            ))
            if verbose:
                for post in issues['title_too_long']:
                    self.stdout.write(f'   - "{post.title}" ({len(post.title)} chars)')
        
        if issues['title_too_short']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["title_too_short"])} posts with titles < 30 characters'
            ))
            if verbose:
                for post in issues['title_too_short']:
                    self.stdout.write(f'   - "{post.title}" ({len(post.title)} chars)')
        
        if issues['no_category']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["no_category"])} posts without category'
            ))
            if verbose:
                for post in issues['no_category']:
                    self.stdout.write(f'   - "{post.title}"')
        
        if issues['no_tags']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["no_tags"])} posts without tags'
            ))
            if verbose:
                for post in issues['no_tags']:
                    self.stdout.write(f'   - "{post.title}"')
        
        if issues['few_tags']:
            self.stdout.write(self.style.WARNING(
                f'⚠️  {len(issues["few_tags"])} posts with < 3 tags'
            ))
            if verbose:
                for post in issues['few_tags']:
                    self.stdout.write(f'   - "{post.title}" ({post.tags.count()} tags)')
        
        if issues['content_too_short']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["content_too_short"])} posts with < 300 words'
            ))
            if verbose:
                for post in issues['content_too_short']:
                    word_count = len(strip_tags(post.content).split())
                    self.stdout.write(f'   - "{post.title}" ({word_count} words)')
        
        if issues['no_banner']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["no_banner"])} posts without banner image'
            ))
            if verbose:
                for post in issues['no_banner']:
                    self.stdout.write(f'   - "{post.title}"')
        
        if issues['slug_issues']:
            self.stdout.write(self.style.ERROR(
                f'❌ {len(issues["slug_issues"])} posts with slug issues'
            ))
            if verbose:
                for post in issues['slug_issues']:
                    self.stdout.write(f'   - "{post.title}" (slug: {post.slug})')
        
        # Calculate SEO score
        total_checks = len(posts) * 7  # 7 checks per post
        total_issues = sum(len(v) for v in issues.values())
        seo_score = ((total_checks - total_issues) / total_checks * 100) if total_checks > 0 else 0
        
        self.stdout.write(self.style.SUCCESS(f'\n--- SEO Score ---'))
        if seo_score >= 90:
            style = self.style.SUCCESS
            emoji = '🎉'
        elif seo_score >= 70:
            style = self.style.WARNING
            emoji = '👍'
        else:
            style = self.style.ERROR
            emoji = '⚠️'
        
        self.stdout.write(style(f'{emoji} Overall SEO Score: {seo_score:.1f}%\n'))
        
        # Recommendations
        self.stdout.write(self.style.SUCCESS('--- Recommendations ---'))
        self.stdout.write('1. Titles should be 30-60 characters')
        self.stdout.write('2. Each post should have a category')
        self.stdout.write('3. Add 3-5 relevant tags per post')
        self.stdout.write('4. Content should be at least 300 words')
        self.stdout.write('5. Always include a banner image')
        self.stdout.write('6. Ensure slugs are descriptive and unique\n')
