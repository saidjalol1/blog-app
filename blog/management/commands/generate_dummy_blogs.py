import random
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from faker import Faker
from PIL import Image
import io

from blog.models import BlogPost, Tags, Category
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Generate 500 dummy blog posts with tags and banner images"

    def handle(self, *args, **kwargs):
        categories = Category.objects.all()

        if not categories.exists():
            self.stdout.write(self.style.ERROR("No categories found. Add categories first."))
            return

        # Create tags if not enough
        if Tags.objects.count() < 30:
            for _ in range(30):
                Tags.objects.get_or_create(name=fake.word())

        tags = list(Tags.objects.all())

        # Ensure at least one user exists
        if not User.objects.exists():
            User.objects.create_user(
                username="admin",
                password="1234567890"
            )

        self.stdout.write(self.style.SUCCESS("Generating 500 blog posts..."))

        for i in range(5000):
            category = random.choice(categories)

            blog = BlogPost.objects.create(
                title=fake.sentence(nb_words=6),
                content=self.generate_html_content(),
                category=category,
            )

            blog.tags.set(random.sample(tags, random.randint(2, 6)))

            # Generate banner image
            image = self.generate_image()
            blog.banner.save(
                f"banner_{blog.id}.jpg",
                ContentFile(image),
                save=True
            )

            if i % 50 == 0:
                self.stdout.write(f"{i} blogs created...")

        self.stdout.write(self.style.SUCCESS("✅ Successfully created 500 blog posts."))

    def generate_image(self):
        img = Image.new(
            "RGB",
            (1200, 630),
            color=(
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
            )
        )
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()


    def generate_html_content(self):
        paragraphs = "".join(
            f"<p>{fake.paragraph(nb_sentences=5)}</p>"
            for _ in range(random.randint(5, 10))
        )
        return f"""
        <h2>{fake.sentence()}</h2>
        {paragraphs}
        <blockquote>{fake.sentence()}</blockquote>
        """
