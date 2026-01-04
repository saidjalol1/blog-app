from django.test import TestCase
from django.urls import reverse
from blog.models import BlogPost, Category

class HomePageTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Home', image='category_images/test.jpg')
        BlogPost.objects.create(title='Featured', content='<p>hi</p>', banner='blog_banners/test.jpg', category=cat, is_featured=True)
        BlogPost.objects.create(title='LatestPost', content='<p>latest</p>', banner='blog_banners/test2.jpg', category=cat, is_featured=False)

    def test_home_includes_featured_and_categories_and_latest(self):
        resp = self.client.get(reverse('home:home_page'))
        self.assertEqual(resp.status_code, 200)
        # Check that the featured post title is in the rendered HTML
        html = resp.content.decode()
        self.assertIn('Featured', html)
        # Category is rendered
        self.assertIn('Home', html)
        # Latest post appears in latest posts slider
        self.assertIn('LatestPost', html)
