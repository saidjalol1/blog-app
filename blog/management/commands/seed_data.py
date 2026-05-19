"""
Seed the database with rich, realistic test data including downloaded images.

Usage:
    python manage.py seed_data          # Seed everything (default 30 posts)
    python manage.py seed_data --posts 50  # Custom post count
    python manage.py seed_data --clear  # Clear existing data first
"""

import os
import io
import random
import uuid
import urllib.request
import urllib.error
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from faker import Faker

fake = Faker()


# ── Category definitions with Unsplash-style image keywords ──────────────────
CATEGORIES = [
    {"name": "Technology", "query": "technology-computer"},
    {"name": "Business", "query": "business-office"},
    {"name": "Design", "query": "design-art"},
    {"name": "Lifestyle", "query": "lifestyle-people"},
    {"name": "Science", "query": "science-laboratory"},
    {"name": "Travel", "query": "travel-landscape"},
    {"name": "Health", "query": "health-fitness"},
    {"name": "Education", "query": "education-books"},
]

# ── Tags ─────────────────────────────────────────────────────────────────────
TAG_NAMES = [
    "Python", "JavaScript", "AI", "Machine Learning", "Web Development",
    "Mobile", "Cloud", "DevOps", "Cybersecurity", "Blockchain",
    "Startup", "Marketing", "Productivity", "Remote Work", "Leadership",
    "UI/UX", "Typography", "Branding", "Photography", "Architecture",
    "Fitness", "Nutrition", "Mental Health", "Meditation", "Travel Tips",
    "Science News", "Space", "Climate", "Innovation", "Data Science",
]

# ── Rich blog post templates ─────────────────────────────────────────────────
POST_TEMPLATES = [
    {
        "title": "The Future of {tech} in {year}: What Experts Predict",
        "category": "Technology",
        "tags": ["AI", "Machine Learning", "Innovation", "Data Science"],
        "vars": {"tech": ["Artificial Intelligence", "Quantum Computing", "Edge Computing", "5G Networks", "Autonomous Vehicles"], "year": ["2026", "2027", "2030"]},
    },
    {
        "title": "How to Build a {framework} Application from Scratch",
        "category": "Technology",
        "tags": ["Web Development", "JavaScript", "Python"],
        "vars": {"framework": ["React", "Django", "Next.js", "Vue.js", "FastAPI", "Flask"]},
    },
    {
        "title": "{num} Essential {topic} Tips for Developers in {year}",
        "category": "Technology",
        "tags": ["Python", "JavaScript", "Web Development", "DevOps"],
        "vars": {"num": ["10", "15", "7", "12"], "topic": ["Python", "JavaScript", "CSS", "Git", "Docker", "TypeScript"], "year": ["2026"]},
    },
    {
        "title": "Understanding {concept}: A Complete Beginner's Guide",
        "category": "Technology",
        "tags": ["AI", "Cloud", "DevOps", "Cybersecurity"],
        "vars": {"concept": ["Kubernetes", "GraphQL", "WebAssembly", "Microservices", "CI/CD Pipelines", "Serverless Architecture"]},
    },
    {
        "title": "How {company_type} Are Using {tech} to Transform Their Business",
        "category": "Business",
        "tags": ["Startup", "Innovation", "Leadership", "Marketing"],
        "vars": {"company_type": ["Startups", "Fortune 500 Companies", "Small Businesses", "E-commerce Brands"], "tech": ["AI", "Blockchain", "Cloud Computing", "Big Data"]},
    },
    {
        "title": "The Ultimate Guide to {topic} for Entrepreneurs",
        "category": "Business",
        "tags": ["Startup", "Marketing", "Productivity", "Leadership"],
        "vars": {"topic": ["Digital Marketing", "Fundraising", "Building a Remote Team", "Product-Market Fit", "Financial Planning"]},
    },
    {
        "title": "{num} {topic} Strategies That Actually Work in {year}",
        "category": "Business",
        "tags": ["Marketing", "Startup", "Productivity", "Remote Work"],
        "vars": {"num": ["8", "5", "12", "10"], "topic": ["Growth Hacking", "Content Marketing", "SEO", "Email Marketing", "Social Media"], "year": ["2026"]},
    },
    {
        "title": "Modern {topic} Trends That Will Define {year}",
        "category": "Design",
        "tags": ["UI/UX", "Typography", "Branding", "Photography"],
        "vars": {"topic": ["Web Design", "UI/UX", "Graphic Design", "Motion Design", "Logo Design"], "year": ["2026", "2027"]},
    },
    {
        "title": "Creating Stunning {type} with {tool}: A Step-by-Step Tutorial",
        "category": "Design",
        "tags": ["UI/UX", "Branding", "Typography", "Photography"],
        "vars": {"type": ["Landing Pages", "Brand Identities", "Illustrations", "Social Media Graphics"], "tool": ["Figma", "Adobe XD", "Photoshop", "Blender"]},
    },
    {
        "title": "The Art of {concept} in Modern Design",
        "category": "Design",
        "tags": ["UI/UX", "Typography", "Architecture", "Photography"],
        "vars": {"concept": ["Color Theory", "Minimalism", "Dark Mode", "Responsive Typography", "3D Design", "Glassmorphism"]},
    },
    {
        "title": "{num} Life-Changing {topic} Habits You Should Start Today",
        "category": "Lifestyle",
        "tags": ["Fitness", "Nutrition", "Mental Health", "Meditation"],
        "vars": {"num": ["7", "10", "5", "12"], "topic": ["Morning", "Productivity", "Wellness", "Mindfulness", "Sleep"]},
    },
    {
        "title": "How I {achievement} in {timeframe}: A Personal Journey",
        "category": "Lifestyle",
        "tags": ["Productivity", "Mental Health", "Fitness", "Remote Work"],
        "vars": {"achievement": ["Learned a New Language", "Ran a Marathon", "Built a Side Business", "Read 100 Books", "Lost 30 Pounds"], "timeframe": ["6 Months", "One Year", "90 Days"]},
    },
    {
        "title": "The Science Behind {topic}: What Research Tells Us",
        "category": "Science",
        "tags": ["Science News", "Innovation", "Data Science", "Climate"],
        "vars": {"topic": ["Sleep", "Creativity", "Exercise", "Nutrition", "Memory", "Happiness"]},
    },
    {
        "title": "Breaking: {discovery} Could Change Everything We Know About {field}",
        "category": "Science",
        "tags": ["Science News", "Space", "Innovation", "Climate"],
        "vars": {"discovery": ["New Material Discovery", "Quantum Breakthrough", "Gene Therapy Advance", "Dark Matter Detection"], "field": ["Physics", "Medicine", "Space Exploration", "Climate Science"]},
    },
    {
        "title": "{num} Hidden Gems in {place}: A Local's Guide",
        "category": "Travel",
        "tags": ["Travel Tips", "Photography", "Lifestyle"],
        "vars": {"num": ["10", "15", "7", "20"], "place": ["Tokyo", "Barcelona", "Istanbul", "Bali", "Marrakech", "Lisbon", "Tashkent", "Samarkand"]},
    },
    {
        "title": "Complete Travel Guide: Exploring {place} on a Budget",
        "category": "Travel",
        "tags": ["Travel Tips", "Photography", "Lifestyle"],
        "vars": {"place": ["Southeast Asia", "Eastern Europe", "South America", "Central Asia", "Scandinavia", "Morocco"]},
    },
    {
        "title": "How {method} Can Improve Your {aspect} in Just {time}",
        "category": "Health",
        "tags": ["Fitness", "Nutrition", "Mental Health", "Meditation"],
        "vars": {"method": ["Intermittent Fasting", "HIIT Training", "Yoga", "Cold Exposure", "Journaling"], "aspect": ["Mental Clarity", "Physical Health", "Energy Levels", "Sleep Quality"], "time": ["30 Days", "2 Weeks", "One Month"]},
    },
    {
        "title": "The Complete Guide to {topic} for Students and Professionals",
        "category": "Education",
        "tags": ["Productivity", "Python", "Data Science", "AI"],
        "vars": {"topic": ["Learning to Code", "Data Analysis", "Public Speaking", "Speed Reading", "Online Courses", "Technical Writing"]},
    },
    {
        "title": "Why {topic} Is the Most Important Skill of {year}",
        "category": "Education",
        "tags": ["AI", "Productivity", "Leadership", "Innovation"],
        "vars": {"topic": ["Critical Thinking", "Emotional Intelligence", "Data Literacy", "Adaptability", "Communication"], "year": ["2026", "the Decade"]},
    },
    {
        "title": "Inside the World of {topic}: An In-Depth Analysis",
        "category": "Technology",
        "tags": ["Cybersecurity", "Blockchain", "Cloud", "DevOps"],
        "vars": {"topic": ["Open Source", "SaaS", "Fintech", "EdTech", "HealthTech", "Green Tech"]},
    },
]


def generate_html_content(title, category):
    """Generate rich, realistic HTML blog content."""
    paragraphs = random.randint(6, 12)
    
    content = f'<p class="lead">{fake.paragraph(nb_sentences=4)}</p>\n\n'
    
    for i in range(paragraphs):
        section_type = random.choice(['text', 'text', 'text', 'heading_text', 'list', 'quote', 'code'])
        
        if section_type == 'text':
            content += f'<p>{fake.paragraph(nb_sentences=random.randint(4, 8))}</p>\n\n'
        
        elif section_type == 'heading_text':
            heading = fake.sentence(nb_words=random.randint(4, 8)).rstrip('.')
            content += f'<h2>{heading}</h2>\n'
            content += f'<p>{fake.paragraph(nb_sentences=random.randint(4, 7))}</p>\n\n'
        
        elif section_type == 'list':
            list_title = fake.sentence(nb_words=random.randint(3, 6)).rstrip('.')
            content += f'<h3>{list_title}</h3>\n<ul>\n'
            for _ in range(random.randint(4, 8)):
                content += f'  <li><strong>{fake.sentence(nb_words=3).rstrip(".")}:</strong> {fake.sentence()}</li>\n'
            content += '</ul>\n\n'
        
        elif section_type == 'quote':
            content += f'<blockquote><p>"{fake.paragraph(nb_sentences=2)}"</p>'
            content += f'<footer>— {fake.name()}, {fake.job()}</footer></blockquote>\n\n'
        
        elif section_type == 'code' and category in ['Technology', 'Education']:
            lang = random.choice(['python', 'javascript', 'bash'])
            if lang == 'python':
                code = f'''def {fake.word()}_{fake.word()}(data):
    """Process the incoming data."""
    results = []
    for item in data:
        if item.is_valid():
            results.append(item.transform())
    return results'''
            elif lang == 'javascript':
                code = f'''const {fake.word()}{fake.word().capitalize()} = async (params) => {{
  const response = await fetch('/api/data', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify(params)
  }});
  return response.json();
}};'''
            else:
                code = f'''# Install dependencies
pip install django faker pillow

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver 0.0.0.0:8000'''
            content += f'<pre><code class="language-{lang}">{code}</code></pre>\n\n'
    
    # Conclusion
    content += f'<h2>Conclusion</h2>\n'
    content += f'<p>{fake.paragraph(nb_sentences=5)}</p>\n'
    content += f'<p><em>{fake.paragraph(nb_sentences=2)}</em></p>\n'
    
    return content


def download_image(query, width, height, retries=3):
    """Download a random image from picsum.photos. Returns bytes or None."""
    for attempt in range(retries):
        try:
            # picsum.photos gives a random image each time, no API key needed
            url = f"https://picsum.photos/{width}/{height}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Django Seed Script)'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return None


def generate_image_with_pillow(width, height, text="", color=None):
    """Fallback: generate a colored image with text using Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    
    if color is None:
        color = (
            random.randint(30, 200),
            random.randint(30, 200),
            random.randint(30, 200),
        )
    
    # Create gradient-like image
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Add some visual interest with rectangles
    for _ in range(random.randint(3, 8)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = x1 + random.randint(50, 300), y1 + random.randint(50, 200)
        overlay_color = (
            min(255, color[0] + random.randint(-40, 40)),
            min(255, color[1] + random.randint(-40, 40)),
            min(255, color[2] + random.randint(-40, 40)),
        )
        draw.rectangle([x1, y1, x2, y2], fill=overlay_color)
    
    # Add text
    if text:
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (width - tw) // 2
        y = (height - th) // 2
        
        # Text shadow
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0), font=font)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


COMMENT_TEMPLATES = [
    "Great article! I learned a lot about {topic}.",
    "This is exactly what I was looking for. Very well explained!",
    "I've been working with {topic} for years and this is one of the best overviews I've seen.",
    "Thanks for sharing this. The section about {detail} was particularly helpful.",
    "Interesting perspective on {topic}. I'd love to see a follow-up article.",
    "I've bookmarked this for future reference. Really comprehensive guide!",
    "Could you elaborate more on {detail}? I'm a bit confused about that part.",
    "Excellent writing! Clear, concise, and packed with useful information.",
    "I shared this with my team. We're implementing some of these ideas already.",
    "As someone new to {topic}, this was incredibly helpful. Thank you!",
    "The code examples are spot on. Tested them and they work perfectly.",
    "I disagree with the point about {detail}, but overall a solid article.",
    "This changed my perspective on {topic}. Well done!",
    "Been following your blog for a while. This is your best post yet!",
    "Very practical advice. I appreciate the real-world examples.",
    "Quality content like this is hard to find. Keep it up!",
    "The comparison between the different approaches was really eye-opening.",
    "I wish I had found this article sooner. Would have saved me hours of research.",
    "Brilliantly written! The examples really help drive the points home.",
    "This is going straight into my notes. Fantastic resource!",
]


class Command(BaseCommand):
    help = 'Seed the database with rich test data including images'

    def add_arguments(self, parser):
        parser.add_argument('--posts', type=int, default=30, help='Number of blog posts to create (default: 30)')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
        parser.add_argument('--no-download', action='store_true', help='Use generated images instead of downloading')

    def handle(self, *args, **options):
        from blog.models import BlogPost, Category, Tags, Comment, Like, Dislike
        
        num_posts = options['posts']
        clear = options['clear']
        no_download = options['no_download']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Like.objects.all().delete()
            Dislike.objects.all().delete()
            Comment.objects.all().delete()
            BlogPost.objects.all().delete()
            Category.objects.all().delete()
            Tags.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared all existing data'))

        # ── 1. Create Tags ───────────────────────────────────────────────────
        self.stdout.write('\n📌 Creating tags...')
        tags_map = {}
        for tag_name in TAG_NAMES:
            tag, created = Tags.objects.get_or_create(name=tag_name)
            tags_map[tag_name] = tag
            if created:
                self.stdout.write(f'  + {tag_name}')
        self.stdout.write(self.style.SUCCESS(f'✓ {len(tags_map)} tags ready'))

        # ── 2. Create Categories with images ─────────────────────────────────
        self.stdout.write('\n📁 Creating categories with images...')
        cat_map = {}
        cat_colors = [
            (41, 128, 185), (39, 174, 96), (192, 57, 43), (142, 68, 173),
            (243, 156, 18), (44, 62, 80), (22, 160, 133), (211, 84, 0),
        ]
        for i, cat_data in enumerate(CATEGORIES):
            cat, created = Category.objects.get_or_create(name=cat_data['name'])
            if created or not cat.image:
                self.stdout.write(f'  Downloading image for {cat_data["name"]}...')
                img_bytes = None
                if not no_download:
                    img_bytes = download_image(cat_data['query'], 800, 600)
                
                if img_bytes is None:
                    self.stdout.write(f'  Generating image for {cat_data["name"]}...')
                    img_bytes = generate_image_with_pillow(800, 600, cat_data['name'], cat_colors[i])
                
                filename = f'{slugify(cat_data["name"])}.jpg'
                cat.image.save(filename, ContentFile(img_bytes), save=True)
                self.stdout.write(f'  ✓ {cat_data["name"]}')
            else:
                self.stdout.write(f'  ○ {cat_data["name"]} (exists)')
            cat_map[cat_data['name']] = cat
        self.stdout.write(self.style.SUCCESS(f'✓ {len(cat_map)} categories ready'))

        # ── 3. Create Blog Posts ─────────────────────────────────────────────
        self.stdout.write(f'\n📝 Creating {num_posts} blog posts with images...')
        posts_created = []
        
        for i in range(num_posts):
            template = random.choice(POST_TEMPLATES)
            
            # Generate title from template
            title = template['title']
            for var_name, var_options in template['vars'].items():
                title = title.replace('{' + var_name + '}', random.choice(var_options), 1)
            
            # Skip if title already exists
            slug = slugify(title)[:200]
            if BlogPost.objects.filter(slug=slug).exists():
                title = f"{title} — {fake.word().capitalize()} Edition"
                slug = slugify(title)[:200]
            
            if BlogPost.objects.filter(slug=slug).exists():
                continue
            
            # Generate content
            category_name = template['category']
            content = generate_html_content(title, category_name)
            
            # Download/generate banner image
            self.stdout.write(f'  [{i+1}/{num_posts}] {title[:60]}...')
            img_bytes = None
            if not no_download:
                img_bytes = download_image(category_name.lower(), 1200, 630)
            
            if img_bytes is None:
                color = cat_colors[CATEGORIES.index(next(c for c in CATEGORIES if c['name'] == category_name)) % len(cat_colors)]
                img_bytes = generate_image_with_pillow(1200, 630, title[:40], color)
            
            # Create the post
            post = BlogPost(
                title=title,
                content=content,
                category=cat_map[category_name],
                is_featured=random.random() < 0.15,  # ~15% featured
                view_count=random.randint(50, 15000),
                slug=slug,
            )
            banner_filename = f'{slug[:80]}.jpg'
            post.banner.save(banner_filename, ContentFile(img_bytes), save=False)
            
            # Override auto_now_add for varied dates
            post.save()
            # Vary the published date over the last 6 months
            days_ago = random.randint(0, 180)
            pub_date = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            BlogPost.objects.filter(pk=post.pk).update(published_date=pub_date)
            
            # Assign tags
            post_tags = [tags_map[t] for t in template['tags'] if t in tags_map]
            # Add 1-3 random extra tags
            extra = random.sample([t for t in tags_map.values() if t not in post_tags], min(3, len(tags_map) - len(post_tags)))
            post.tags.set(post_tags + extra)
            
            posts_created.append(post)
            
            # Small delay to get different images from picsum
            if not no_download and (i + 1) % 5 == 0:
                time.sleep(0.5)
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(posts_created)} blog posts created'))

        # ── 4. Create Comments ───────────────────────────────────────────────
        self.stdout.write('\n💬 Creating comments...')
        comment_count = 0
        for post in posts_created:
            num_comments = random.randint(1, 8)
            for _ in range(num_comments):
                topic = post.category.name.lower()
                detail = fake.sentence(nb_words=3).rstrip('.')
                template_text = random.choice(COMMENT_TEMPLATES)
                comment_text = template_text.format(topic=topic, detail=detail)
                
                Comment.objects.create(
                    blog_post=post,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    content=comment_text,
                    visitor_id=str(uuid.uuid4()),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    is_approved=random.random() < 0.9,  # 90% approved
                )
                comment_count += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {comment_count} comments created'))

        # ── 5. Create Likes and Dislikes ─────────────────────────────────────
        self.stdout.write('\n👍 Creating likes and dislikes...')
        like_count = 0
        dislike_count = 0
        for post in posts_created:
            num_likes = random.randint(3, 30)
            num_dislikes = random.randint(0, 5)
            
            for _ in range(num_likes):
                try:
                    Like.objects.create(
                        blog_post=post,
                        visitor_id=str(uuid.uuid4()),
                    )
                    like_count += 1
                except Exception:
                    pass
            
            for _ in range(num_dislikes):
                try:
                    Dislike.objects.create(
                        blog_post=post,
                        visitor_id=str(uuid.uuid4()),
                    )
                    dislike_count += 1
                except Exception:
                    pass
        
        self.stdout.write(self.style.SUCCESS(f'✓ {like_count} likes, {dislike_count} dislikes created'))

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Database seeding complete!'))
        self.stdout.write(f'  📁 Categories:  {Category.objects.count()}')
        self.stdout.write(f'  📌 Tags:        {Tags.objects.count()}')
        self.stdout.write(f'  📝 Blog Posts:  {BlogPost.objects.count()}')
        self.stdout.write(f'  ⭐ Featured:    {BlogPost.objects.filter(is_featured=True).count()}')
        self.stdout.write(f'  💬 Comments:    {Comment.objects.count()}')
        self.stdout.write(f'  👍 Likes:       {Like.objects.count()}')
        self.stdout.write(f'  👎 Dislikes:    {Dislike.objects.count()}')
        self.stdout.write('=' * 60)
