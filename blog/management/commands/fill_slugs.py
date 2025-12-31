from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from django.db.models import Q

from blog.models import BlogPost


class Command(BaseCommand):
    help = "Fill missing slugs for BlogPost by slugifying the title and ensuring uniqueness."

    def handle(self, *args, **options):
        qs = BlogPost.objects.filter(Q(slug__isnull=True) | Q(slug=""))
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No missing slugs found.'))
            return

        updated = 0
        with transaction.atomic():
            for post in qs.select_for_update():
                base = slugify(post.title)[:200] or 'post'
                slug = base
                i = 1
                while BlogPost.objects.filter(slug=slug).exclude(pk=post.pk).exists():
                    slug = f"{base}-{i}"
                    i += 1
                post.slug = slug
                post.save(update_fields=['slug'])
                updated += 1
                self.stdout.write(f'Updated post {post.pk}: slug="{post.slug}"')

        self.stdout.write(self.style.SUCCESS(f'Done. {updated} posts updated.'))
