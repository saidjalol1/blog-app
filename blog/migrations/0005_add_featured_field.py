"""Add is_featured field to BlogPost"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_add_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='is_featured',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
