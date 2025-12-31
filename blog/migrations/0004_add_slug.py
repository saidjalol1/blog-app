# Generated manually: add slug field and backfill existing posts
from django.db import migrations, models
from django.utils.text import slugify


def generate_unique_slug(apps, schema_editor):
    BlogPost = apps.get_model('blog', 'BlogPost')
    for post in BlogPost.objects.all():
        if not post.slug:
            base = slugify(post.title)[:200] or 'post'
            slug = base
            count = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base}-{count}"
                count += 1
            post.slug = slug
            post.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_category_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(blank=True, max_length=255),
        ),
        migrations.RunPython(generate_unique_slug, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(unique=True, max_length=255),
        ),
    ]
