from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from blog.models import BlogPost, Category, Tags

@override_settings(MEDIA_ROOT='/tmp', CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class FetchBlogsAPITest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Technology')
        self.tag1 = Tags.objects.create(name='ai-ml')
        self.tag2 = Tags.objects.create(name='productivity')
        # create some posts
        for i in range(5):
            banner = SimpleUploadedFile(f"banner_{i}.jpg", b"filecontent", content_type="image/jpeg")
            post = BlogPost.objects.create(title=f"Post {i}", content=f"<p>content {i}</p>", category=self.cat, banner=banner)
            post.tags.add(self.tag1, self.tag2)

    def test_fetch_blogs_default(self):
        url = reverse('blog:fetch_blogs')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)
        self.assertIn('page', data)
        self.assertIn('total', data)
        self.assertGreaterEqual(data['total'], 5)
        # ensure slug is included in serialized posts
        self.assertIn('slug', data['results'][0])

    def test_fetch_blogs_filters_and_pagination(self):
        url = reverse('blog:fetch_blogs')
        resp = self.client.get(url, {'per_page': 2, 'page': 2, 'categories': 'Technology', 'tags': 'ai-ml'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['page'], 2)
        self.assertEqual(data['per_page'], 2)
        self.assertIn('results', data)
        self.assertLessEqual(len(data['results']), 2)

    def test_fetch_filters_returns_categories_and_tags(self):
        url = reverse('blog:fetch_filters')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('categories', data)
        self.assertIn('tags', data)
        # categories should include Technology with at least 1 post
        tech = next((c for c in data['categories'] if c['name'] == 'Technology'), None)
        self.assertIsNotNone(tech)
        self.assertGreaterEqual(tech['post_count'], 1)
        # tags should include ai-ml and productivity
        t1 = next((t for t in data['tags'] if t['name'] == 'ai-ml'), None)
        t2 = next((t for t in data['tags'] if t['name'] == 'productivity'), None)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertGreaterEqual(t1['post_count'], 1)
        self.assertGreaterEqual(t2['post_count'], 1)

    def test_post_detail_and_json(self):
        # pick a post id
        post = BlogPost.objects.first()
        url = reverse('blog:blog_post_detail', args=[post.slug])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, post.title)
        # Ensure OG meta tags are present for SEO
        self.assertIn('<meta property="og:title"', resp.content.decode())

        urlj = reverse('blog:blog_post_json', args=[post.slug])
        respj = self.client.get(urlj)
        self.assertEqual(respj.status_code, 200)
        data = respj.json()
        self.assertEqual(data['id'], post.pk)
        self.assertEqual(data['title'], post.title)
        self.assertEqual(data.get('slug'), post.slug)

    def test_blog_page_filters_by_category(self):
        # Create two categories and posts
        cat1 = Category.objects.create(name='FilteredCat', image='category_images/f1.jpg')
        cat2 = Category.objects.create(name='OtherCat', image='category_images/f2.jpg')
        p1 = BlogPost.objects.create(title='InCat', content='<p>in</p>', banner='blog_banners/a.jpg', category=cat1)
        p2 = BlogPost.objects.create(title='OutCat', content='<p>out</p>', banner='blog_banners/b.jpg', category=cat2)
        url = reverse('blog:blog_page') + '?categories=FilteredCat'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('InCat', html)
        self.assertNotIn('OutCat', html)
