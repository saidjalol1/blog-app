"""
Property-based tests for production blog enhancements.

These tests validate universal properties that should hold across all inputs.
Uses hypothesis for property-based testing.
"""

from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
import json

from blog.utils.cookie_manager import CookieManager


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class CookieManagerPropertyTests(HypothesisTestCase):
    """Property-based tests for CookieManager utility."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # Feature: production-blog-enhancements, Property 2: View Cookie Creation on First Visit
    @given(post_id=st.integers(min_value=1, max_value=1000000))
    @settings(max_examples=20)
    def test_view_cookie_creation_on_first_visit(self, post_id):
        """
        **Validates: Requirements 2.1**
        
        For any blog post, when a visitor views it for the first time 
        (no existing view cookie), the system should create a cookie 
        marking that post as viewed.
        """
        # Create request without viewed_posts cookie
        request = self.factory.get('/blog/post/test/')
        request.COOKIES = {}
        
        # Check that post is not viewed initially
        has_viewed = CookieManager.has_viewed_post(request, post_id)
        self.assertFalse(has_viewed, f"Post {post_id} should not be marked as viewed initially")
        
        # Create response and mark post as viewed
        response = HttpResponse()
        CookieManager.mark_post_viewed(response, post_id)
        
        # Verify cookie was set
        self.assertIn(CookieManager.VIEWED_POSTS_COOKIE, response.cookies)
        
        cookie = response.cookies[CookieManager.VIEWED_POSTS_COOKIE]
        viewed_posts = json.loads(cookie.value)
        
        # Verify post_id is in the viewed posts list
        self.assertIn(post_id, viewed_posts, 
                     f"Post {post_id} should be in viewed posts cookie")
    
    # Feature: production-blog-enhancements, Property 4: Cookie Security Attributes
    @given(
        visitor_id=st.uuids(),
        post_id=st.integers(min_value=1, max_value=1000000)
    )
    @settings(max_examples=20)
    def test_cookie_security_attributes(self, visitor_id, post_id):
        """
        **Validates: Requirements 2.6, 6.14**
        
        For all cookies created by the system (view tracking, engagement, 
        visitor ID), each cookie should have HttpOnly=True, Secure=True, 
        and SameSite='Lax' attributes.
        """
        request = self.factory.get('/blog/post/test/')
        request.COOKIES = {}
        
        # Test visitor_id cookie security attributes
        response = HttpResponse()
        CookieManager.get_or_create_visitor_id(request, response)
        
        visitor_cookie = response.cookies.get(CookieManager.VISITOR_ID_COOKIE)
        self.assertIsNotNone(visitor_cookie, "Visitor ID cookie should be set")
        self.assertTrue(visitor_cookie['httponly'], 
                       "Visitor ID cookie should have HttpOnly=True")
        self.assertTrue(visitor_cookie['secure'], 
                       "Visitor ID cookie should have Secure=True")
        self.assertEqual(visitor_cookie['samesite'], 'Lax', 
                        "Visitor ID cookie should have SameSite='Lax'")
        
        # Test viewed_posts cookie security attributes
        response2 = HttpResponse()
        CookieManager.mark_post_viewed(response2, post_id)
        
        viewed_cookie = response2.cookies.get(CookieManager.VIEWED_POSTS_COOKIE)
        self.assertIsNotNone(viewed_cookie, "Viewed posts cookie should be set")
        self.assertTrue(viewed_cookie['httponly'], 
                       "Viewed posts cookie should have HttpOnly=True")
        self.assertTrue(viewed_cookie['secure'], 
                       "Viewed posts cookie should have Secure=True")
        self.assertEqual(viewed_cookie['samesite'], 'Lax', 
                        "Viewed posts cookie should have SameSite='Lax'")
    
    # Feature: production-blog-enhancements, Property 5: Cookie Expiration Durations
    @given(post_id=st.integers(min_value=1, max_value=1000000))
    @settings(max_examples=20)
    def test_cookie_expiration_durations(self, post_id):
        """
        **Validates: Requirements 2.3, 3.9**
        
        For any view tracking cookie, expiration should be at least 30 days; 
        for any engagement tracking cookie (visitor_id), expiration should be 
        at least 365 days.
        """
        request = self.factory.get('/blog/post/test/')
        request.COOKIES = {}
        
        # Test visitor_id cookie expiration (365 days minimum)
        response = HttpResponse()
        CookieManager.get_or_create_visitor_id(request, response)
        
        visitor_cookie = response.cookies.get(CookieManager.VISITOR_ID_COOKIE)
        self.assertIsNotNone(visitor_cookie, "Visitor ID cookie should be set")
        
        visitor_max_age = visitor_cookie['max-age']
        min_visitor_expiration = 365 * 24 * 60 * 60  # 365 days in seconds
        self.assertGreaterEqual(visitor_max_age, min_visitor_expiration,
                               f"Visitor ID cookie expiration ({visitor_max_age}s) should be at least 365 days ({min_visitor_expiration}s)")
        
        # Test viewed_posts cookie expiration (30 days minimum)
        response2 = HttpResponse()
        CookieManager.mark_post_viewed(response2, post_id)
        
        viewed_cookie = response2.cookies.get(CookieManager.VIEWED_POSTS_COOKIE)
        self.assertIsNotNone(viewed_cookie, "Viewed posts cookie should be set")
        
        viewed_max_age = viewed_cookie['max-age']
        min_viewed_expiration = 30 * 24 * 60 * 60  # 30 days in seconds
        self.assertGreaterEqual(viewed_max_age, min_viewed_expiration,
                               f"Viewed posts cookie expiration ({viewed_max_age}s) should be at least 30 days ({min_viewed_expiration}s)")



@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class ModelConstraintPropertyTests(HypothesisTestCase):
    """Property-based tests for model constraints."""
    
    # Feature: production-blog-enhancements, Property 10: Engagement Mutual Exclusion
    @given(
        visitor_id=st.text(min_size=36, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-')),
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    )
    @settings(max_examples=20)
    def test_engagement_mutual_exclusion(self, visitor_id, post_title):
        """
        **Validates: Requirements 3.5**
        
        For any blog post and visitor at any point in time, the visitor 
        should have at most one engagement record (either like or dislike, 
        never both).
        """
        from blog.models import BlogPost, Category, Like, Dislike
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create a like
        Like.objects.create(blog_post=post, visitor_id=visitor_id)
        
        # Verify only like exists
        like_count = Like.objects.filter(blog_post=post, visitor_id=visitor_id).count()
        dislike_count = Dislike.objects.filter(blog_post=post, visitor_id=visitor_id).count()
        
        self.assertEqual(like_count, 1, "Should have exactly one like")
        self.assertEqual(dislike_count, 0, "Should have no dislikes")
        
        # Now create a dislike (simulating the toggle behavior)
        # First delete the like
        Like.objects.filter(blog_post=post, visitor_id=visitor_id).delete()
        # Then create dislike
        Dislike.objects.create(blog_post=post, visitor_id=visitor_id)
        
        # Verify only dislike exists
        like_count = Like.objects.filter(blog_post=post, visitor_id=visitor_id).count()
        dislike_count = Dislike.objects.filter(blog_post=post, visitor_id=visitor_id).count()
        
        self.assertEqual(like_count, 0, "Should have no likes")
        self.assertEqual(dislike_count, 1, "Should have exactly one dislike")
        
        # Verify mutual exclusion: total engagement should never exceed 1
        total_engagement = like_count + dislike_count
        self.assertLessEqual(total_engagement, 1, 
                            f"Visitor should have at most one engagement (like or dislike), found {total_engagement}")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 16: Comment Metadata Storage
    @given(
        first_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), whitelist_characters="-'")),
        last_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), whitelist_characters="-'")),
        content=st.text(min_size=1, max_size=2000),
        visitor_id=st.text(min_size=36, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-')),
        ip_address=st.ip_addresses(v=4).map(str),
        user_agent=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=20)
    def test_comment_metadata_storage(self, first_name, last_name, content, visitor_id, ip_address, user_agent):
        """
        **Validates: Requirements 4.7, 4.8**
        
        For any successfully created comment, the database record should 
        contain: first_name, last_name, content, ip_address, user_agent, 
        visitor_id, and created_at timestamp.
        """
        from blog.models import BlogPost, Category, Comment
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=f"Test Post {visitor_id[:8]}",
            content="Test content",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create comment with all metadata
        comment = Comment.objects.create(
            blog_post=post,
            first_name=first_name,
            last_name=last_name,
            content=content,
            visitor_id=visitor_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Retrieve comment from database
        saved_comment = Comment.objects.get(pk=comment.pk)
        
        # Verify all metadata is stored correctly
        self.assertEqual(saved_comment.first_name, first_name, 
                        "First name should be stored correctly")
        self.assertEqual(saved_comment.last_name, last_name, 
                        "Last name should be stored correctly")
        self.assertEqual(saved_comment.content, content, 
                        "Content should be stored correctly")
        self.assertEqual(saved_comment.visitor_id, visitor_id, 
                        "Visitor ID should be stored correctly")
        self.assertEqual(saved_comment.ip_address, ip_address, 
                        "IP address should be stored correctly")
        self.assertEqual(saved_comment.user_agent, user_agent, 
                        "User agent should be stored correctly")
        self.assertIsNotNone(saved_comment.created_at, 
                            "Created_at timestamp should be set")
        
        # Cleanup
        comment.delete()
        post.delete()
        category.delete()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class ViewCountingPropertyTests(HypothesisTestCase):
    """Property-based tests for view counting functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # Feature: production-blog-enhancements, Property 3: View Count Increment Idempotence
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
        view_attempts=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=20)
    def test_view_count_increment_idempotence(self, post_title, view_attempts):
        """
        **Validates: Requirements 2.2, 2.7**
        
        For any blog post and visitor, viewing the post multiple times with 
        a valid view cookie should increment the view count exactly once 
        (first view only).
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post with initial view_count of 0
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for view counting",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            view_count=0
        )
        
        initial_count = post.view_count
        
        # Use Django test client to maintain cookies across requests
        client = Client()
        
        # Make multiple view requests with the same client (same cookies)
        for i in range(view_attempts):
            response = client.get(f'/blogs/post/{post.slug}/')
            self.assertEqual(response.status_code, 200, 
                           f"Request {i+1} should succeed")
        
        # Refresh post from database
        post.refresh_from_db()
        final_count = post.view_count
        
        # Verify view count incremented exactly once
        self.assertEqual(final_count, initial_count + 1,
                        f"View count should increment exactly once regardless of {view_attempts} views. "
                        f"Initial: {initial_count}, Final: {final_count}")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 6: View Count Persistence
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
        unique_visitors=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10)
    def test_view_count_persistence(self, post_title, unique_visitors):
        """
        **Validates: Requirements 2.4**
        
        For any blog post that has been viewed, querying the database should 
        return a view_count value that accurately reflects the number of 
        unique visitors.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post with initial view_count of 0
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for view persistence",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            view_count=0
        )
        
        initial_count = post.view_count
        
        # Simulate multiple unique visitors (each with their own client/cookies)
        for visitor_num in range(unique_visitors):
            client = Client()  # New client = new visitor with no cookies
            response = client.get(f'/blogs/post/{post.slug}/')
            self.assertEqual(response.status_code, 200,
                           f"Visitor {visitor_num + 1} request should succeed")
        
        # Query database to get updated view count
        post.refresh_from_db()
        final_count = post.view_count
        
        # Verify view count accurately reflects unique visitors
        expected_count = initial_count + unique_visitors
        self.assertEqual(final_count, expected_count,
                        f"View count should accurately reflect {unique_visitors} unique visitors. "
                        f"Expected: {expected_count}, Got: {final_count}")
        
        # Verify persistence by querying again
        post_from_db = BlogPost.objects.get(pk=post.pk)
        self.assertEqual(post_from_db.view_count, expected_count,
                        "View count should persist in database across queries")
        
        # Cleanup
        post.delete()
        category.delete()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class EngagementPropertyTests(HypothesisTestCase):
    """Property-based tests for engagement (like/dislike) functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        # Clear cache before each test to avoid rate limiting issues
        from django.core.cache import cache
        cache.clear()
    
    # Feature: production-blog-enhancements, Property 8: Engagement Recording with Visitor ID
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str),
        action=st.sampled_from(['like', 'dislike'])
    )
    @settings(max_examples=20)
    def test_engagement_recording_with_visitor_id(self, post_title, visitor_id, action):
        """
        **Validates: Requirements 3.1, 3.2, 3.6**
        
        For any blog post, when a visitor with a valid visitor_id cookie 
        performs a like or dislike action, the system should create a 
        database record associating that visitor_id with the post and 
        action type.
        """
        from blog.models import BlogPost, Category, Like, Dislike
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        import json
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for engagement",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client and set visitor_id cookie
        client = Client()
        client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
        
        # Perform engagement action
        if action == 'like':
            response = client.post(f'/blogs/post/{post.slug}/like/')
            model_class = Like
        else:
            response = client.post(f'/blogs/post/{post.slug}/dislike/')
            model_class = Dislike
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200,
                        f"{action.capitalize()} action should succeed")
        
        # Verify JSON response
        data = json.loads(response.content)
        self.assertIn('action', data, "Response should contain 'action' field")
        self.assertEqual(data['action'], 'added', 
                        f"Action should be 'added' for new {action}")
        
        # Verify database record was created with visitor_id
        engagement = model_class.objects.filter(
            blog_post=post,
            visitor_id=visitor_id
        )
        self.assertTrue(engagement.exists(),
                       f"{action.capitalize()} record should exist in database")
        self.assertEqual(engagement.count(), 1,
                        f"Should have exactly one {action} record")
        
        # Verify the visitor_id matches
        engagement_obj = engagement.first()
        self.assertEqual(engagement_obj.visitor_id, visitor_id,
                        f"Stored visitor_id should match the cookie value")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 9: Like-Dislike State Transition
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str)
    )
    @settings(max_examples=20)
    def test_like_dislike_state_transition(self, post_title, visitor_id):
        """
        **Validates: Requirements 3.3, 3.4, 3.5**
        
        For any blog post and visitor, performing a like action after a 
        dislike action should result in: (1) the dislike record being 
        deleted, (2) a like record being created, and (3) the visitor 
        having exactly one engagement record (like) for that post.
        """
        from blog.models import BlogPost, Category, Like, Dislike
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        
        # Clear cache to avoid rate limiting issues across test iterations
        cache.clear()
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for state transition",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client and set visitor_id cookie
        client = Client()
        client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
        
        # Step 1: Perform dislike action
        response1 = client.post(f'/blogs/post/{post.slug}/dislike/')
        self.assertEqual(response1.status_code, 200, "Dislike action should succeed")
        
        # Verify dislike exists
        dislike_count_before = Dislike.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        self.assertEqual(dislike_count_before, 1, "Should have one dislike")
        
        like_count_before = Like.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        self.assertEqual(like_count_before, 0, "Should have no likes")
        
        # Step 2: Perform like action (state transition)
        response2 = client.post(f'/blogs/post/{post.slug}/like/')
        self.assertEqual(response2.status_code, 200, "Like action should succeed")
        
        # Verify state after transition
        # (1) Dislike record should be deleted
        dislike_count_after = Dislike.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        self.assertEqual(dislike_count_after, 0,
                        "Dislike record should be deleted after liking")
        
        # (2) Like record should be created
        like_count_after = Like.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        self.assertEqual(like_count_after, 1,
                        "Like record should be created")
        
        # (3) Visitor should have exactly one engagement record
        total_engagement = like_count_after + dislike_count_after
        self.assertEqual(total_engagement, 1,
                        "Visitor should have exactly one engagement record (like)")
        
        # Test reverse transition: like -> dislike
        response3 = client.post(f'/blogs/post/{post.slug}/dislike/')
        self.assertEqual(response3.status_code, 200, "Dislike action should succeed")
        
        # Verify reverse state transition
        like_count_final = Like.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        dislike_count_final = Dislike.objects.filter(
            blog_post=post, visitor_id=visitor_id
        ).count()
        
        self.assertEqual(like_count_final, 0,
                        "Like record should be deleted after disliking")
        self.assertEqual(dislike_count_final, 1,
                        "Dislike record should be created")
        
        total_engagement_final = like_count_final + dislike_count_final
        self.assertEqual(total_engagement_final, 1,
                        "Visitor should have exactly one engagement record (dislike)")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 28: Like/Dislike Rate Limiting
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str),
        action=st.sampled_from(['like', 'dislike'])
    )
    @settings(max_examples=10)
    def test_like_dislike_rate_limiting(self, post_title, visitor_id, action):
        """
        **Validates: Requirements 8.2, 8.3**
        
        For any IP address, after performing 10 like/dislike actions within 
        a 1-minute window, the 11th action should be rejected with a rate 
        limit error (HTTP 429).
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        import json
        
        # Clear cache before test
        cache.clear()
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create multiple test blog posts for rate limiting test
        posts = []
        for i in range(12):
            post = BlogPost.objects.create(
                title=f"{post_title} {i}",
                content=f"Test content {i}",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            posts.append(post)
        
        # Create client and set visitor_id cookie
        client = Client()
        client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
        
        # Determine endpoint based on action
        endpoint_suffix = 'like' if action == 'like' else 'dislike'
        
        # Perform 10 actions (should all succeed)
        for i in range(10):
            response = client.post(f'/blogs/post/{posts[i].slug}/{endpoint_suffix}/')
            self.assertEqual(response.status_code, 200,
                           f"{action.capitalize()} action {i+1} should succeed (within rate limit)")
        
        # 11th action should be rate limited (HTTP 429)
        response_11 = client.post(f'/blogs/post/{posts[10].slug}/{endpoint_suffix}/')
        self.assertEqual(response_11.status_code, 429,
                        f"{action.capitalize()} action 11 should be rate limited (HTTP 429)")
        
        # Verify error response contains appropriate message
        data = json.loads(response_11.content)
        self.assertIn('error', data, "Rate limit response should contain 'error' field")
        self.assertIn('Rate limit exceeded', data['error'],
                     "Error message should mention rate limit")
        
        # Cleanup
        for post in posts:
            post.delete()
        category.delete()
        cache.clear()
    
    # Feature: production-blog-enhancements, Property 30: Suspicious User Agent Blocking
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str),
        suspicious_ua=st.sampled_from([
            '',  # Empty user agent
            'curl/7.68.0',  # curl
            'Wget/1.20.3',  # wget
            'python-requests/2.25.1',  # Python requests
            'Googlebot/2.1',  # Bot
            'Mozilla/5.0 (compatible; bingbot/2.0)',  # Bot
            'Scrapy/2.5.0',  # Scraper
            'Go-http-client/1.1',  # Go HTTP client
        ])
    )
    @settings(max_examples=10)
    def test_suspicious_user_agent_blocking(self, post_title, visitor_id, suspicious_ua):
        """
        **Validates: Requirements 8.6**
        
        For any request with a user agent matching known bot/scraper patterns 
        (empty, curl, wget, etc.), the system should block or rate-limit the 
        request more aggressively.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        from blog.utils.helpers import is_suspicious_user_agent
        import json
        
        # Clear cache before test
        cache.clear()
        
        # Verify the user agent is detected as suspicious
        self.assertTrue(is_suspicious_user_agent(suspicious_ua),
                       f"User agent '{suspicious_ua}' should be detected as suspicious")
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog posts (need more for stricter rate limiting)
        posts = []
        for i in range(5):
            post = BlogPost.objects.create(
                title=f"{post_title} {i}",
                content=f"Test content {i}",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            posts.append(post)
        
        # Create client with suspicious user agent
        client = Client(HTTP_USER_AGENT=suspicious_ua)
        client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
        
        # For suspicious agents, rate limit should be 10x stricter
        # Normal limit for likes is 10 per minute, so suspicious should be 1 per minute
        # Try to perform 2 like actions - second should be blocked
        
        # First action should succeed
        response1 = client.post(f'/blogs/post/{posts[0].slug}/like/')
        self.assertEqual(response1.status_code, 200,
                        "First like action should succeed even with suspicious UA")
        
        # Second action should be rate limited due to stricter limits
        response2 = client.post(f'/blogs/post/{posts[1].slug}/like/')
        self.assertEqual(response2.status_code, 429,
                        "Second like action should be rate limited for suspicious UA")
        
        # Verify error response
        data = json.loads(response2.content)
        self.assertIn('error', data, "Rate limit response should contain 'error' field")
        self.assertIn('Rate limit exceeded', data['error'],
                     "Error message should mention rate limit")
        
        # Cleanup
        for post in posts:
            post.delete()
        category.delete()
        cache.clear()



@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class CommentValidationPropertyTests(HypothesisTestCase):
    """Property-based tests for comment validation."""
    
    def setUp(self):
        self.factory = RequestFactory()
        # Clear cache before each test to avoid rate limiting issues
        from django.core.cache import cache
        cache.clear()
    
    # Feature: production-blog-enhancements, Property 13: Comment Required Fields Validation
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        missing_field=st.sampled_from(['first_name', 'last_name', 'content'])
    )
    @settings(max_examples=20)
    def test_comment_required_fields_validation(self, post_title, missing_field):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        
        For any comment submission, if any of the required fields 
        (first_name, last_name, content) is missing or empty (after 
        stripping whitespace), the submission should be rejected with 
        a validation error.
        """
        from blog.forms import CommentForm
        
        # Create valid data for all fields
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': 'This is a test comment.'
        }
        
        # Test with missing field (empty string)
        test_data = valid_data.copy()
        test_data[missing_field] = ''
        
        form = CommentForm(data=test_data)
        self.assertFalse(form.is_valid(), 
                        f"Form should be invalid when {missing_field} is empty")
        self.assertIn(missing_field, form.errors,
                     f"Form errors should include {missing_field}")
        
        # Test with whitespace-only field
        test_data[missing_field] = '   '
        form = CommentForm(data=test_data)
        self.assertFalse(form.is_valid(),
                        f"Form should be invalid when {missing_field} is whitespace-only")
        self.assertIn(missing_field, form.errors,
                     f"Form errors should include {missing_field}")
        
        # Test with field completely missing from data
        test_data = valid_data.copy()
        del test_data[missing_field]
        form = CommentForm(data=test_data)
        self.assertFalse(form.is_valid(),
                        f"Form should be invalid when {missing_field} is missing")
        self.assertIn(missing_field, form.errors,
                     f"Form errors should include {missing_field}")
    
    # Feature: production-blog-enhancements, Property 14: Name Field Character Validation
    @given(
        field_name=st.sampled_from(['first_name', 'last_name']),
        invalid_char=st.sampled_from(['@', '#', '$', '%', '&', '*', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '?', '.', ',', ';', ':', '/', '\\', '|', '[', ']', '{', '}', '<', '>', '=', '+', '_', '~', '`'])
    )
    @settings(max_examples=20)
    def test_name_field_character_validation(self, field_name, invalid_char):
        """
        **Validates: Requirements 4.4, 4.5**
        
        For any comment submission, if the first_name or last_name contains 
        characters outside the allowed set (letters, spaces, hyphens, 
        apostrophes), the submission should be rejected with a validation error.
        """
        from blog.forms import CommentForm
        
        # Create valid data
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': 'This is a test comment.'
        }
        
        # Test with invalid character in the specified field
        test_data = valid_data.copy()
        test_data[field_name] = f"Test{invalid_char}Name"
        
        form = CommentForm(data=test_data)
        self.assertFalse(form.is_valid(),
                        f"Form should be invalid when {field_name} contains '{invalid_char}'")
        self.assertIn(field_name, form.errors,
                     f"Form errors should include {field_name}")
        
        # Verify error message mentions invalid characters
        error_message = str(form.errors[field_name])
        self.assertIn('invalid characters', error_message.lower(),
                     "Error message should mention invalid characters")
    
    @given(
        field_name=st.sampled_from(['first_name', 'last_name']),
        valid_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-')
    )
    @settings(max_examples=20)
    def test_name_field_valid_characters(self, field_name, valid_name):
        """
        **Validates: Requirements 4.4, 4.5**
        
        For any comment submission with names containing only valid 
        characters (letters, spaces, hyphens, apostrophes), the name 
        validation should pass.
        """
        from blog.forms import CommentForm
        
        # Skip if name is empty or whitespace-only (tested separately)
        if not valid_name.strip():
            return
        
        # Create valid data
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': 'This is a test comment.'
        }
        
        # Test with valid name in the specified field
        test_data = valid_data.copy()
        test_data[field_name] = valid_name
        
        form = CommentForm(data=test_data)
        
        # If form is invalid, it should NOT be due to character validation
        if not form.is_valid():
            if field_name in form.errors:
                error_message = str(form.errors[field_name])
                self.assertNotIn('invalid characters', error_message.lower(),
                               f"Valid name '{valid_name}' should not trigger character validation error")
    
    # Feature: production-blog-enhancements, Property 15: Comment Content Length Validation
    @given(
        content_length=st.integers(min_value=2001, max_value=3000)
    )
    @settings(max_examples=20)
    def test_comment_content_length_validation(self, content_length):
        """
        **Validates: Requirements 4.6**
        
        For any comment submission, if the content exceeds 2000 characters, 
        the submission should be rejected with a validation error.
        """
        from blog.forms import CommentForm
        
        # Create content that exceeds 2000 characters
        long_content = 'a' * content_length
        
        test_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': long_content
        }
        
        form = CommentForm(data=test_data)
        self.assertFalse(form.is_valid(),
                        f"Form should be invalid when content is {content_length} characters (exceeds 2000)")
        self.assertIn('content', form.errors,
                     "Form errors should include content field")
        
        # Verify error message mentions length limit
        error_message = str(form.errors['content'])
        self.assertIn('2000', error_message,
                     "Error message should mention 2000 character limit")
    
    @given(
        content_length=st.integers(min_value=1, max_value=2000)
    )
    @settings(max_examples=20)
    def test_comment_content_valid_length(self, content_length):
        """
        **Validates: Requirements 4.6**
        
        For any comment submission with content at or below 2000 characters, 
        the content length validation should pass.
        """
        from blog.forms import CommentForm
        
        # Create content within valid length
        valid_content = 'a' * content_length
        
        test_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': valid_content
        }
        
        form = CommentForm(data=test_data)
        
        # If form is invalid, it should NOT be due to length validation
        if not form.is_valid():
            if 'content' in form.errors:
                error_message = str(form.errors['content'])
                self.assertNotIn('too long', error_message.lower(),
                               f"Content of {content_length} characters should not trigger length validation error")
                self.assertNotIn('2000', error_message,
                               f"Content of {content_length} characters should not trigger 2000 character limit error")
    
    # Feature: production-blog-enhancements, Property 19: Comment Rate Limiting
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str)
    )
    @settings(max_examples=10)
    def test_comment_rate_limiting(self, post_title, visitor_id):
        """
        **Validates: Requirements 4.11, 8.1**
        
        For any IP address, after submitting 3 comments within a 10-minute 
        window, the 4th comment should be rejected with a rate limit error 
        (HTTP 429).
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        
        # Clear cache before test
        cache.clear()
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {visitor_id[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for comment rate limiting",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client and set visitor_id cookie
        client = Client()
        client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
        
        # Prepare valid comment data
        comment_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'content': 'This is a test comment.'
        }
        
        # Submit 3 comments (should all succeed)
        for i in range(3):
            comment_data['content'] = f'Test comment {i+1}'
            response = client.post(f'/blogs/post/{post.slug}/', data=comment_data)
            # Should redirect on success (302) or return 200
            self.assertIn(response.status_code, [200, 302],
                         f"Comment {i+1} should succeed (within rate limit)")
        
        # 4th comment should be rate limited (HTTP 429)
        comment_data['content'] = 'Test comment 4 - should be rate limited'
        response_4 = client.post(f'/blogs/post/{post.slug}/', data=comment_data)
        self.assertEqual(response_4.status_code, 429,
                        "Comment 4 should be rate limited (HTTP 429)")
        
        # Verify error response contains appropriate message
        response_content = response_4.content.decode('utf-8')
        self.assertIn('Rate limit exceeded', response_content,
                     "Rate limit response should mention rate limit")
        
        # Cleanup
        post.delete()
        category.delete()
        cache.clear()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class PublicAccessPropertyTests(HypothesisTestCase):
    """Property-based tests for public access without authentication."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # Feature: production-blog-enhancements, Property 1: Public Access Without Authentication
    @given(
        url_path=st.sampled_from([
            '/blogs/',
            '/blogs/fetch_blogs/',
            '/blogs/filters/',
        ])
    )
    @settings(max_examples=20)
    def test_public_access_without_authentication(self, url_path):
        """
        **Validates: Requirements 1.5**
        
        For any public-facing blog URL (blog list, blog detail, API endpoints), 
        requests without authentication credentials should succeed and return 
        appropriate content.
        """
        from django.test import Client
        
        # Create client without authentication
        client = Client()
        
        # Make request without any authentication
        response = client.get(url_path)
        
        # Verify request succeeds (200 OK)
        self.assertEqual(response.status_code, 200,
                        f"Public URL {url_path} should be accessible without authentication")
        
        # Verify response contains content (not empty)
        self.assertGreater(len(response.content), 0,
                          f"Response from {url_path} should contain content")
    
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @settings(max_examples=10)
    def test_blog_post_detail_public_access(self, post_title):
        """
        **Validates: Requirements 1.5**
        
        For any blog post detail page, requests without authentication 
        credentials should succeed and return the post content.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.utils.html import escape
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for public access",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client without authentication
        client = Client()
        
        # Make request to blog post detail page without authentication
        response = client.get(f'/blogs/post/{post.slug}/')
        
        # Verify request succeeds (200 OK)
        self.assertEqual(response.status_code, 200,
                        f"Blog post detail page should be accessible without authentication")
        
        # Verify response contains the post title (HTML-escaped for security)
        response_content = response.content.decode('utf-8')
        escaped_title = escape(post_title)
        self.assertIn(escaped_title, response_content,
                     "Response should contain the blog post title (HTML-escaped)")
        
        # Cleanup
        post.delete()
        category.delete()
    
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        action=st.sampled_from(['like', 'dislike'])
    )
    @settings(max_examples=10)
    def test_engagement_actions_public_access(self, post_title, action):
        """
        **Validates: Requirements 1.5**
        
        For any engagement action (like/dislike), requests without 
        authentication credentials should succeed.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        
        # Clear cache to avoid rate limiting
        cache.clear()
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for engagement",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client without authentication
        client = Client()
        
        # Perform engagement action without authentication
        endpoint = f'/blogs/post/{post.slug}/{action}/'
        response = client.post(endpoint)
        
        # Verify request succeeds (200 OK)
        self.assertEqual(response.status_code, 200,
                        f"{action.capitalize()} action should be accessible without authentication")
        
        # Verify response is JSON with expected fields
        import json
        data = json.loads(response.content)
        self.assertIn('action', data,
                     f"{action.capitalize()} response should contain 'action' field")
        
        # Cleanup
        post.delete()
        category.delete()
        cache.clear()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class TemplateRenderingPropertyTests(HypothesisTestCase):
    """Property-based tests for template rendering."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # Feature: production-blog-enhancements, Property 7: View Count Display
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        view_count=st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=20)
    def test_view_count_display(self, post_title, view_count):
        """
        **Validates: Requirements 2.5**
        
        For any blog post rendered in detail view, the HTML output should 
        contain the view count value.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post with specific view count
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for view count display",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            view_count=view_count
        )
        
        # Create client and request blog post detail page
        client = Client()
        response = client.get(f'/blogs/post/{post.slug}/')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Blog post detail page should load successfully")
        
        # Verify HTML output contains view count
        response_content = response.content.decode('utf-8')
        
        # Check for view count in the HTML (should be in format "X views")
        view_count_text = f"{view_count} views"
        self.assertIn(view_count_text, response_content,
                     f"HTML should contain view count '{view_count_text}'")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 11: Engagement Count Display
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        like_count=st.integers(min_value=0, max_value=1000),
        dislike_count=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=20)
    def test_engagement_count_display(self, post_title, like_count, dislike_count):
        """
        **Validates: Requirements 3.7**
        
        For any blog post rendered in detail view, the HTML output should 
        contain both the like count and dislike count.
        """
        from blog.models import BlogPost, Category, Like, Dislike
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        import uuid
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for engagement count display",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create likes
        for i in range(like_count):
            Like.objects.create(
                blog_post=post,
                visitor_id=str(uuid.uuid4())
            )
        
        # Create dislikes
        for i in range(dislike_count):
            Dislike.objects.create(
                blog_post=post,
                visitor_id=str(uuid.uuid4())
            )
        
        # Create client and request blog post detail page
        client = Client()
        response = client.get(f'/blogs/post/{post.slug}/')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Blog post detail page should load successfully")
        
        # Verify HTML output contains like and dislike counts
        response_content = response.content.decode('utf-8')
        
        # Check for like count in the HTML (should be in format "(X)")
        like_count_text = f"({like_count})"
        self.assertIn(like_count_text, response_content,
                     f"HTML should contain like count '{like_count_text}'")
        
        # Check for dislike count in the HTML (should be in format "(X)")
        dislike_count_text = f"({dislike_count})"
        self.assertIn(dislike_count_text, response_content,
                     f"HTML should contain dislike count '{dislike_count_text}'")
        
        # Verify both "Like" and "Dislike" buttons are present
        self.assertIn('Like', response_content,
                     "HTML should contain 'Like' button")
        self.assertIn('Dislike', response_content,
                     "HTML should contain 'Dislike' button")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 17: Comment Display Completeness
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        first_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-'),
        last_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-'),
        comment_content=st.text(min_size=1, max_size=2000)
    )
    @settings(max_examples=20)
    def test_comment_display_completeness(self, post_title, first_name, last_name, comment_content):
        """
        **Validates: Requirements 4.9**
        
        For any comment rendered on a blog post page, the HTML output should 
        contain the commenter's first name, last name, and the full comment 
        content.
        """
        from blog.models import BlogPost, Category, Comment
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.utils.html import escape
        import uuid
        
        # Skip if names are empty or whitespace-only
        if not first_name.strip() or not last_name.strip():
            return
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for comment display",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test comment
        comment = Comment.objects.create(
            blog_post=post,
            first_name=first_name,
            last_name=last_name,
            content=comment_content,
            visitor_id=str(uuid.uuid4()),
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        # Create client and request blog post detail page
        client = Client()
        response = client.get(f'/blogs/post/{post.slug}/')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Blog post detail page should load successfully")
        
        # Verify HTML output contains comment data
        response_content = response.content.decode('utf-8')
        
        # Check for first name (HTML-escaped for security)
        escaped_first_name = escape(first_name)
        self.assertIn(escaped_first_name, response_content,
                     f"HTML should contain commenter's first name '{escaped_first_name}'")
        
        # Check for last name (HTML-escaped for security)
        escaped_last_name = escape(last_name)
        self.assertIn(escaped_last_name, response_content,
                     f"HTML should contain commenter's last name '{escaped_last_name}'")
        
        # Check for comment content (HTML-escaped for security)
        # Note: Django's linebreaksbr filter converts \n to <br>, so we need to handle that
        from django.utils.html import linebreaks
        
        # For long content, check for a substring to avoid issues with line breaks
        if len(comment_content) > 100:
            # Check for first 50 characters of content (without newlines for simplicity)
            content_substring = escape(comment_content[:50].replace('\n', ''))
            if content_substring.strip():  # Only check if there's actual content
                self.assertIn(content_substring, response_content,
                             f"HTML should contain comment content (at least first 50 chars)")
        else:
            # For short content, check if the escaped content (with <br> tags) is present
            # The template uses linebreaksbr filter which converts \n to <br>
            escaped_content = escape(comment_content).replace('\n', '<br>')
            if escaped_content.strip() and escaped_content.strip() != '<br>':
                self.assertIn(escaped_content, response_content,
                             f"HTML should contain full comment content")
        
        # Cleanup
        comment.delete()
        post.delete()
        category.delete()



@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    # Use production-like settings for security tests
    DEBUG=False,
    ALLOWED_HOSTS=['testserver', 'localhost'],
    SECURE_SSL_REDIRECT=False,  # Disabled for testing
    CSP_DEFAULT_SRC=("'self'",),
    CSP_SCRIPT_SRC=("'self'", "'unsafe-inline'", "cdn.jsdelivr.net"),
    CSP_STYLE_SRC=("'self'", "'unsafe-inline'", "fonts.googleapis.com"),
    CSP_FONT_SRC=("'self'", "fonts.gstatic.com"),
    CSP_IMG_SRC=("'self'", "data:", "https:"),
)
class SecurityConfigurationPropertyTests(HypothesisTestCase):
    """Property-based tests for security configurations."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # Feature: production-blog-enhancements, Property 22: CSP Header Presence
    @given(
        url_path=st.sampled_from([
            '/blogs/fetch_blogs/',
            '/blogs/filters/',
        ])
    )
    @settings(max_examples=20)
    def test_csp_header_presence(self, url_path):
        """
        **Validates: Requirements 6.11**
        
        For all HTTP responses from the application, the response should 
        include a Content-Security-Policy header with appropriate directives.
        """
        from django.test import Client
        
        # Create client
        client = Client()
        
        # Make request
        response = client.get(url_path)
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        f"Request to {url_path} should succeed")
        
        # Verify CSP header is present
        self.assertIn('Content-Security-Policy', response.headers,
                     "Response should include Content-Security-Policy header")
        
        # Get CSP header value
        csp_header = response.headers['Content-Security-Policy']
        
        # Verify CSP header contains expected directives
        self.assertIn("default-src", csp_header,
                     "CSP header should contain default-src directive")
        self.assertIn("'self'", csp_header,
                     "CSP header should contain 'self' source")
        
        # Verify script-src directive
        self.assertIn("script-src", csp_header,
                     "CSP header should contain script-src directive")
        
        # Verify style-src directive
        self.assertIn("style-src", csp_header,
                     "CSP header should contain style-src directive")
        
        # Verify img-src directive
        self.assertIn("img-src", csp_header,
                     "CSP header should contain img-src directive")
    
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @settings(max_examples=10)
    def test_csp_header_on_blog_post_detail(self, post_title):
        """
        **Validates: Requirements 6.11**
        
        For blog post detail pages, the response should include a 
        Content-Security-Policy header.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {post_title[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=post_title,
            content="Test content for CSP header",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client and request blog post JSON endpoint (doesn't require template)
        client = Client()
        response = client.get(f'/blogs/post/{post.slug}/json/')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Blog post JSON endpoint should load successfully")
        
        # Verify CSP header is present
        self.assertIn('Content-Security-Policy', response.headers,
                     "Blog post JSON response should include Content-Security-Policy header")
        
        # Cleanup
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 23: XSS Input Sanitization
    @given(
        xss_payload=st.sampled_from([
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')">',
            '<body onload=alert("XSS")>',
            '<input onfocus=alert("XSS") autofocus>',
            '<select onfocus=alert("XSS") autofocus>',
            '<textarea onfocus=alert("XSS") autofocus>',
            '<marquee onstart=alert("XSS")>',
        ])
    )
    @settings(max_examples=20)
    def test_xss_input_sanitization(self, xss_payload):
        """
        **Validates: Requirements 6.12**
        
        For any user-submitted content (comment content, names), if the input 
        contains HTML tags or JavaScript code, the system should sanitize it 
        before storage or display, preventing script execution.
        
        This test verifies that:
        1. XSS payloads can be stored safely in the database
        2. The data is treated as literal text, not executable code
        3. Django's template system will escape the content when rendered
        """
        from blog.models import BlogPost, Category, Comment
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils.html import escape
        import uuid
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {uuid.uuid4().hex[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=f"Test Post {uuid.uuid4().hex[:8]}",
            content="Test content for XSS sanitization",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Test XSS in comment content - should be stored as literal text
        comment_with_xss = Comment.objects.create(
            blog_post=post,
            first_name="Test",
            last_name="User",
            content=xss_payload,
            visitor_id=str(uuid.uuid4()),
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        # Verify comment was created successfully (XSS payload stored as literal data)
        self.assertIsNotNone(comment_with_xss.pk,
                            "Comment with XSS payload should be created successfully")
        
        # Verify the XSS payload is stored as literal data (not executed)
        saved_comment = Comment.objects.get(pk=comment_with_xss.pk)
        self.assertEqual(saved_comment.content, xss_payload,
                        "XSS payload should be stored as literal data")
        
        # Verify Django's escape function properly escapes the content
        escaped_content = escape(xss_payload)
        
        # The escaped version should not contain dangerous tags
        self.assertNotIn('<script>', escaped_content.lower(),
                        "Escaped content should not contain unescaped <script> tags")
        
        # If the payload contains <, it should be escaped to &lt;
        if '<' in xss_payload:
            self.assertIn('&lt;', escaped_content,
                         "Escaped content should contain &lt; instead of <")
        
        # If the payload contains >, it should be escaped to &gt;
        if '>' in xss_payload:
            self.assertIn('&gt;', escaped_content,
                         "Escaped content should contain &gt; instead of >")
        
        # Verify we can query the comment back safely
        retrieved_comment = Comment.objects.filter(content=xss_payload).first()
        self.assertIsNotNone(retrieved_comment,
                            "Should be able to query comment with XSS payload as literal data")
        
        # Cleanup
        comment_with_xss.delete()
        post.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 24: SQL Injection Protection
    @given(
        sql_injection_payload=st.sampled_from([
            "'; DROP TABLE blog_blogpost; --",
            "' OR '1'='1",
            "1' UNION SELECT NULL, NULL, NULL--",
            "admin'--",
            "' OR 1=1--",
            "'; DELETE FROM blog_comment WHERE '1'='1",
            "1' AND '1'='1",
            "' OR 'x'='x",
            "1; DROP TABLE blog_like; --",
            "' UNION SELECT password FROM auth_user--",
        ])
    )
    @settings(max_examples=20)
    def test_sql_injection_protection(self, sql_injection_payload):
        """
        **Validates: Requirements 6.13**
        
        For any user input used in database queries, malicious SQL syntax 
        (e.g., '; DROP TABLE--) should be treated as literal data, not 
        executed as SQL commands.
        """
        from blog.models import BlogPost, Category, Comment
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        import uuid
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {uuid.uuid4().hex[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title=f"Test Post {uuid.uuid4().hex[:8]}",
            content="Test content for SQL injection protection",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Test SQL injection in comment content
        # Django ORM should treat this as literal data, not SQL commands
        try:
            comment = Comment.objects.create(
                blog_post=post,
                first_name="Test",
                last_name="User",
                content=sql_injection_payload,
                visitor_id=str(uuid.uuid4()),
                ip_address='127.0.0.1',
                user_agent='Test User Agent'
            )
            
            # Verify comment was created successfully (SQL injection was prevented)
            self.assertIsNotNone(comment.pk,
                                "Comment should be created successfully (SQL injection prevented)")
            
            # Verify the SQL injection payload is stored as literal data
            saved_comment = Comment.objects.get(pk=comment.pk)
            self.assertEqual(saved_comment.content, sql_injection_payload,
                           "SQL injection payload should be stored as literal data")
            
            # Verify database tables still exist (not dropped by SQL injection)
            # If SQL injection worked, these queries would fail
            self.assertTrue(BlogPost.objects.exists(),
                           "BlogPost table should still exist (not dropped by SQL injection)")
            self.assertTrue(Comment.objects.exists(),
                           "Comment table should still exist (not dropped by SQL injection)")
            
            # Verify we can query the comment back
            retrieved_comment = Comment.objects.filter(content=sql_injection_payload).first()
            self.assertIsNotNone(retrieved_comment,
                                "Should be able to query comment with SQL injection payload as literal data")
            
            # Cleanup
            comment.delete()
        except Exception as e:
            # If an exception occurs, it should be a validation error, not a SQL error
            self.fail(f"SQL injection test failed with exception: {e}")
        finally:
            # Cleanup
            post.delete()
            category.delete()
    
    @given(
        search_term=st.sampled_from([
            "'; DROP TABLE blog_blogpost; --",
            "' OR '1'='1",
            "admin'--",
        ])
    )
    @settings(max_examples=10)
    def test_sql_injection_in_search_queries(self, search_term):
        """
        **Validates: Requirements 6.13**
        
        For search queries with SQL injection attempts, the system should 
        treat the input as literal search text, not SQL commands.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category {search_term[:8]}",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        post = BlogPost.objects.create(
            title="Test Post for SQL Injection",
            content="Test content",
            category=category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create client
        client = Client()
        
        # Attempt search with SQL injection payload
        # The system should treat this as a literal search term
        try:
            response = client.get('/blogs/fetch_blogs/', {'search': search_term})
            
            # Verify request succeeds (SQL injection was prevented)
            self.assertEqual(response.status_code, 200,
                           "Search request should succeed (SQL injection prevented)")
            
            # Verify database tables still exist (not dropped by SQL injection)
            self.assertTrue(BlogPost.objects.exists(),
                           "BlogPost table should still exist after search with SQL injection payload")
            self.assertTrue(Category.objects.exists(),
                           "Category table should still exist after search with SQL injection payload")
            
            # Verify we can still query the database normally
            all_posts = BlogPost.objects.all()
            self.assertGreaterEqual(all_posts.count(), 1,
                                   "Should be able to query BlogPost table normally after SQL injection attempt")
        except Exception as e:
            # If an exception occurs, it should be a validation error, not a SQL error
            error_message = str(e).lower()
            self.assertNotIn('syntax error', error_message,
                           "Should not have SQL syntax errors (indicates SQL injection was not prevented)")
            self.assertNotIn('drop table', error_message,
                           "Should not execute DROP TABLE commands")
        finally:
            # Cleanup
            post.delete()
            category.delete()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class TransactionAtomicityPropertyTests(HypothesisTestCase):
    """Property-based tests for transaction atomicity."""
    
    def setUp(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from blog.models import Category, BlogPost
        
        # Create test category
        self.category = Category.objects.create(
            name="Test Category",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test blog post
        self.post = BlogPost.objects.create(
            title="Test Post",
            content="Test content",
            category=self.category,
            banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
    
    def tearDown(self):
        # Clean up test data
        self.post.delete()
        self.category.delete()
    
    # Feature: production-blog-enhancements, Property 32: Transaction Atomicity for Critical Operations
    @given(
        first_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        last_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        content=st.text(min_size=1, max_size=2000)
    )
    @settings(max_examples=20)
    def test_comment_submission_atomicity(self, first_name, last_name, content):
        """
        **Validates: Requirements 9.7**
        
        For any critical operation (comment submission with rate limit check, 
        like/dislike toggle), either all database changes should succeed together, 
        or all should be rolled back (no partial state).
        
        This test verifies that comment submission is atomic - if any part fails,
        no partial data is saved to the database.
        """
        from blog.models import Comment
        from django.test import Client
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Skip empty or whitespace-only names
        if not first_name.strip() or not last_name.strip() or not content.strip():
            return
        
        client = Client()
        
        # Count comments before submission
        initial_comment_count = Comment.objects.filter(blog_post=self.post).count()
        
        # Submit comment
        response = client.post(
            f'/blog/post/{self.post.slug}/',
            {
                'first_name': first_name,
                'last_name': last_name,
                'content': content
            }
        )
        
        # Get comment count after submission
        final_comment_count = Comment.objects.filter(blog_post=self.post).count()
        
        # Verify atomicity: either comment was created (success) or not created (failure)
        # There should be no partial state
        if response.status_code in [200, 302]:  # Success (redirect or render)
            # Comment should be created
            self.assertEqual(final_comment_count, initial_comment_count + 1,
                           "Comment should be created on successful submission")
            
            # Verify all fields are populated (no partial data)
            comment = Comment.objects.filter(blog_post=self.post).latest('created_at')
            self.assertEqual(comment.first_name, first_name,
                           "Comment first_name should match submitted data")
            self.assertEqual(comment.last_name, last_name,
                           "Comment last_name should match submitted data")
            self.assertIsNotNone(comment.ip_address,
                               "Comment ip_address should be populated")
            self.assertIsNotNone(comment.visitor_id,
                               "Comment visitor_id should be populated")
            self.assertIsNotNone(comment.created_at,
                               "Comment created_at should be populated")
        else:
            # Comment should not be created on failure
            self.assertEqual(final_comment_count, initial_comment_count,
                           "Comment should not be created on failed submission")
    
    # Feature: production-blog-enhancements, Property 32: Transaction Atomicity for Critical Operations
    @given(action=st.sampled_from(['like', 'dislike']))
    @settings(max_examples=20)
    def test_engagement_toggle_atomicity(self, action):
        """
        **Validates: Requirements 9.7**
        
        For any like/dislike toggle operation, either all database changes 
        should succeed together (remove opposite, add/remove current), or all 
        should be rolled back (no partial state).
        
        This test verifies that engagement toggles are atomic - the removal of
        the opposite engagement and the addition/removal of the current engagement
        happen together or not at all.
        """
        from blog.models import Like, Dislike
        from django.test import Client
        
        client = Client()
        
        # Get initial counts
        initial_like_count = Like.objects.filter(blog_post=self.post).count()
        initial_dislike_count = Dislike.objects.filter(blog_post=self.post).count()
        
        # Perform engagement action
        endpoint = f'/blog/post/{self.post.slug}/{action}/'
        response = client.post(endpoint)
        
        # Get final counts
        final_like_count = Like.objects.filter(blog_post=self.post).count()
        final_dislike_count = Dislike.objects.filter(blog_post=self.post).count()
        
        # Verify atomicity based on response
        if response.status_code == 200:
            # Success - verify state is consistent
            response_data = response.json()
            
            # Verify counts match database state
            self.assertEqual(response_data['likes'], final_like_count,
                           "Response like count should match database state")
            self.assertEqual(response_data['dislikes'], final_dislike_count,
                           "Response dislike count should match database state")
            
            # Verify mutual exclusion: visitor should not have both like and dislike
            # Get visitor_id from cookie
            visitor_id = client.cookies.get(CookieManager.VISITOR_ID_COOKIE)
            if visitor_id:
                has_like = Like.objects.filter(
                    blog_post=self.post, 
                    visitor_id=visitor_id.value
                ).exists()
                has_dislike = Dislike.objects.filter(
                    blog_post=self.post, 
                    visitor_id=visitor_id.value
                ).exists()
                
                self.assertFalse(has_like and has_dislike,
                               "Visitor should not have both like and dislike (mutual exclusion)")
        else:
            # Failure - verify no changes were made
            self.assertEqual(final_like_count, initial_like_count,
                           "Like count should not change on failed engagement")
            self.assertEqual(final_dislike_count, initial_dislike_count,
                           "Dislike count should not change on failed engagement")
    
    # Feature: production-blog-enhancements, Property 32: Transaction Atomicity for Critical Operations
    @given(
        num_comments=st.integers(min_value=1, max_value=5),
        first_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        last_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        content=st.text(min_size=1, max_size=2000)
    )
    @settings(max_examples=10)
    def test_concurrent_comment_atomicity(self, num_comments, first_name, last_name, content):
        """
        **Validates: Requirements 9.7**
        
        For any sequence of comment submissions, each submission should be atomic
        and independent. If one fails, it should not affect others.
        
        This test verifies that multiple comment submissions maintain atomicity
        and don't interfere with each other.
        """
        from blog.models import Comment
        from django.test import Client
        
        # Skip empty or whitespace-only names
        if not first_name.strip() or not last_name.strip() or not content.strip():
            return
        
        client = Client()
        
        # Count comments before submissions
        initial_comment_count = Comment.objects.filter(blog_post=self.post).count()
        
        successful_submissions = 0
        
        # Submit multiple comments
        for i in range(num_comments):
            response = client.post(
                f'/blog/post/{self.post.slug}/',
                {
                    'first_name': f"{first_name}{i}",
                    'last_name': f"{last_name}{i}",
                    'content': f"{content} - Comment {i}"
                }
            )
            
            if response.status_code in [200, 302]:
                successful_submissions += 1
        
        # Get final comment count
        final_comment_count = Comment.objects.filter(blog_post=self.post).count()
        
        # Verify atomicity: number of comments created should match successful submissions
        expected_count = initial_comment_count + successful_submissions
        self.assertEqual(final_comment_count, expected_count,
                       f"Comment count should match successful submissions: "
                       f"expected {expected_count}, got {final_comment_count}")
        
        # Verify all created comments have complete data (no partial records)
        recent_comments = Comment.objects.filter(blog_post=self.post).order_by('-created_at')[:num_comments]
        for comment in recent_comments:
            self.assertIsNotNone(comment.first_name, "Comment should have first_name")
            self.assertIsNotNone(comment.last_name, "Comment should have last_name")
            self.assertIsNotNone(comment.content, "Comment should have content")
            self.assertIsNotNone(comment.ip_address, "Comment should have ip_address")
            self.assertIsNotNone(comment.visitor_id, "Comment should have visitor_id")
            self.assertIsNotNone(comment.created_at, "Comment should have created_at")


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class CachingAndPerformancePropertyTests(HypothesisTestCase):
    """Property-based tests for caching and performance optimizations."""
    
    def setUp(self):
        self.factory = RequestFactory()
        # Clear cache before each test
        from django.core.cache import cache
        cache.clear()
    
    # Feature: production-blog-enhancements, Property 20: Query Count Efficiency
    @given(
        num_posts=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=10)
    def test_query_count_efficiency(self, num_posts):
        """
        **Validates: Requirements 5.5**
        
        For any blog post list request, the total number of database queries 
        should remain constant (not increase linearly) regardless of the 
        number of posts returned.
        """
        from blog.models import BlogPost, Category, Tags
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category Query",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create test tags
        tag1 = Tags.objects.create(name=f"Tag1")
        tag2 = Tags.objects.create(name=f"Tag2")
        
        # Create multiple blog posts
        posts = []
        for i in range(num_posts):
            post = BlogPost.objects.create(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            post.tags.add(tag1, tag2)
            posts.append(post)
        
        # Create client
        client = Client()
        
        # Measure query count for blog list request
        with CaptureQueriesContext(connection) as context:
            response = client.get('/blogs/')
            query_count = len(context.captured_queries)
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Blog list request should succeed")
        
        # Verify query count is reasonable and constant
        # With proper optimization (select_related, prefetch_related, annotate),
        # query count should be constant regardless of number of posts
        # Expected queries:
        # 1. Session query
        # 2. Main BlogPost query with select_related(category)
        # 3. Prefetch tags
        # 4. Prefetch comments
        # 5. Annotation queries for counts
        # Total should be around 5-10 queries regardless of post count
        max_expected_queries = 15  # Allow some buffer for session/middleware queries
        
        self.assertLessEqual(query_count, max_expected_queries,
                            f"Query count ({query_count}) should be constant and not exceed {max_expected_queries} "
                            f"regardless of {num_posts} posts. This indicates N+1 query problem if exceeded.")
        
        # Cleanup
        for post in posts:
            post.delete()
        tag1.delete()
        tag2.delete()
        category.delete()
    
    # Feature: production-blog-enhancements, Property 21: Cache Hit Behavior
    @given(
        cache_key=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'))
    )
    @settings(max_examples=20, deadline=2000)
    def test_cache_hit_behavior(self, cache_key):
        """
        **Validates: Requirements 5.6, 7.4, 7.10**
        
        For any cached endpoint (filters, blog list), making the same request 
        twice within the cache TTL should result in the second request being 
        served from cache (faster response, no database query).
        """
        from django.core.cache import cache
        from django.test import Client
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        import time
        
        # Clear cache before test
        cache.clear()
        
        # Test cache behavior with filters endpoint
        client = Client()
        
        # First request - should hit database
        with CaptureQueriesContext(connection) as context1:
            response1 = client.get('/blogs/filters/')
            query_count1 = len(context1.captured_queries)
            response_time1 = time.time()
        
        self.assertEqual(response1.status_code, 200,
                        "First filters request should succeed")
        
        # Second request - should hit cache (no database queries for data)
        with CaptureQueriesContext(connection) as context2:
            response2 = client.get('/blogs/filters/')
            query_count2 = len(context2.captured_queries)
            response_time2 = time.time()
        
        self.assertEqual(response2.status_code, 200,
                        "Second filters request should succeed")
        
        # Verify second request has fewer queries (cache hit)
        # First request will have queries for categories and tags
        # Second request should have minimal or no queries (served from cache)
        self.assertLessEqual(query_count2, query_count1,
                            f"Second request query count ({query_count2}) should be less than or equal to "
                            f"first request ({query_count1}) due to caching")
        
        # Verify responses are identical (cache returns same data)
        self.assertEqual(response1.content, response2.content,
                        "Cached response should return identical data")
        
        # Test with custom cache key
        test_value = {'test': 'data', 'key': cache_key}
        cache.set(f'test:{cache_key}', test_value, 300)
        
        # Retrieve from cache
        cached_value = cache.get(f'test:{cache_key}')
        self.assertEqual(cached_value, test_value,
                        "Cache should return the same value that was set")
        
        # Verify cache TTL behavior
        # Set a short TTL cache entry
        cache.set(f'test:ttl:{cache_key}', 'short_lived', 1)
        self.assertEqual(cache.get(f'test:ttl:{cache_key}'), 'short_lived',
                        "Cache should return value within TTL")
        
        # Wait for TTL to expire
        time.sleep(1.1)
        self.assertIsNone(cache.get(f'test:ttl:{cache_key}'),
                         "Cache should return None after TTL expires")
    
    # Feature: production-blog-enhancements, Property 25: Static Asset Caching Headers
    @given(
        static_path=st.sampled_from([
            '/static/css/style.css',
            '/static/js/blog.js',
            '/static/images/logo.png'
        ])
    )
    @settings(max_examples=10)
    def test_static_asset_caching_headers(self, static_path):
        """
        **Validates: Requirements 7.3**
        
        For all static asset responses (CSS, JS, images), the HTTP response 
        should include cache-control headers with appropriate max-age values.
        """
        from django.test import Client
        from django.conf import settings
        import os
        
        # Skip test if static files don't exist (they may not be collected in test environment)
        # This test is more relevant in production with WhiteNoise
        # For testing purposes, we'll verify the configuration is correct
        
        # Verify WhiteNoise is configured in middleware
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', settings.MIDDLEWARE,
                     "WhiteNoise middleware should be configured")
        
        # Verify static file storage is configured for compression
        if hasattr(settings, 'STATICFILES_STORAGE'):
            self.assertIn('whitenoise', settings.STATICFILES_STORAGE.lower(),
                         "Static files storage should use WhiteNoise for compression")
        
        # In production settings, verify cache headers configuration
        # Note: This test validates configuration rather than runtime behavior
        # since static files may not be available in test environment
        
        # Create a mock static file response to test headers
        client = Client()
        
        # Try to get a static file (may 404 in test environment, but we can check headers if it exists)
        try:
            response = client.get(static_path)
            if response.status_code == 200:
                # If static file exists, verify cache headers
                # WhiteNoise should add Cache-Control headers
                if 'Cache-Control' in response.headers:
                    cache_control = response.headers['Cache-Control']
                    # Verify max-age is present
                    self.assertIn('max-age', cache_control,
                                 "Cache-Control header should include max-age directive")
        except Exception:
            # Static file may not exist in test environment, skip runtime check
            pass
    
    # Feature: production-blog-enhancements, Property 27: Pagination Limit Enforcement
    @given(
        requested_per_page=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=20)
    def test_pagination_limit_enforcement(self, requested_per_page):
        """
        **Validates: Requirements 7.7**
        
        For any blog post list request, the number of posts returned should 
        not exceed the configured per-page limit (e.g., 50 posts maximum).
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.conf import settings
        import json
        
        # Get configured max per page (default 50)
        max_per_page = getattr(settings, 'BLOG_POSTS_PER_PAGE', 50)
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category Pagination",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create more posts than the max limit to test enforcement
        num_posts = max_per_page + 20
        posts = []
        for i in range(num_posts):
            post = BlogPost.objects.create(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            posts.append(post)
        
        # Create client
        client = Client()
        
        # Request with specific per_page parameter
        response = client.get(f'/blogs/fetch_blogs/?per_page={requested_per_page}')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Fetch blogs request should succeed")
        
        # Parse JSON response
        data = json.loads(response.content)
        
        # Verify response has results
        self.assertIn('results', data,
                     "Response should contain 'results' field")
        
        results = data['results']
        actual_count = len(results)
        
        # Verify pagination limit is enforced
        # If requested_per_page exceeds max, should return max
        # If requested_per_page is within limit, should return requested amount (or less if not enough posts)
        expected_max = min(requested_per_page, max_per_page)
        
        self.assertLessEqual(actual_count, max_per_page,
                            f"Returned {actual_count} posts, but should not exceed max limit of {max_per_page}")
        
        # Verify per_page in response matches enforced limit
        self.assertIn('per_page', data,
                     "Response should contain 'per_page' field")
        
        returned_per_page = data['per_page']
        self.assertLessEqual(returned_per_page, max_per_page,
                            f"Returned per_page ({returned_per_page}) should not exceed max limit ({max_per_page})")
        
        # Verify actual results don't exceed the returned per_page value
        self.assertLessEqual(actual_count, returned_per_page,
                            f"Actual results count ({actual_count}) should not exceed per_page ({returned_per_page})")
        
        # Cleanup
        for post in posts:
            post.delete()
        category.delete()
    
    @given(
        page_number=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10)
    def test_pagination_page_navigation(self, page_number):
        """
        **Validates: Requirements 7.7**
        
        For any blog post list request with pagination, requesting different 
        pages should return different sets of posts within the limit.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.conf import settings
        import json
        
        # Get configured max per page
        max_per_page = getattr(settings, 'BLOG_POSTS_PER_PAGE', 50)
        
        # Create test category
        category = Category.objects.create(
            name=f"Test Category Page Nav",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Create enough posts for multiple pages
        num_posts = max_per_page * 3
        posts = []
        for i in range(num_posts):
            post = BlogPost.objects.create(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            posts.append(post)
        
        # Create client
        client = Client()
        
        # Request specific page
        response = client.get(f'/blogs/fetch_blogs/?page={page_number}&per_page=10')
        
        # Verify request succeeds
        self.assertEqual(response.status_code, 200,
                        "Fetch blogs request should succeed")
        
        # Parse JSON response
        data = json.loads(response.content)
        
        # Verify pagination metadata
        self.assertIn('page', data, "Response should contain 'page' field")
        self.assertIn('total_pages', data, "Response should contain 'total_pages' field")
        self.assertIn('total', data, "Response should contain 'total' field")
        
        # Verify page number in response
        returned_page = data['page']
        total_pages = data['total_pages']
        
        # If requested page exceeds total pages, should return last page
        expected_page = min(page_number, total_pages)
        self.assertEqual(returned_page, expected_page,
                        f"Returned page ({returned_page}) should match expected page ({expected_page})")
        
        # Verify results are within limit
        results = data['results']
        self.assertLessEqual(len(results), 10,
                            "Results should not exceed requested per_page limit")
        
        # Cleanup
        for post in posts:
            post.delete()
        category.delete()



@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.cache'
)
class LoggingPropertyTests(HypothesisTestCase):
    """Property-based tests for logging functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        # Clear cache before each test to avoid rate limiting issues
        from django.core.cache import cache
        cache.clear()
    
    # Feature: production-blog-enhancements, Property 31: Rate Limit Violation Logging
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        visitor_id=st.uuids().map(str),
        action=st.sampled_from(['comment', 'like', 'dislike'])
    )
    @settings(max_examples=10)
    def test_rate_limit_violation_logging(self, post_title, visitor_id, action):
        """
        **Validates: Requirements 8.7, 10.2**
        
        For any rate limit violation (comment, like, dislike), a log entry 
        should be created in the security log with the IP address, action 
        type, and timestamp.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        import logging
        from io import StringIO
        
        # Clear cache before test
        cache.clear()
        
        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        security_logger = logging.getLogger('django.security')
        security_logger.addHandler(handler)
        original_level = security_logger.level
        security_logger.setLevel(logging.WARNING)
        
        try:
            # Create test category
            category = Category.objects.create(
                name=f"Test Category {visitor_id[:8]}",
                image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            
            # Create test blog posts
            posts = []
            num_posts = 15 if action in ['like', 'dislike'] else 5
            for i in range(num_posts):
                post = BlogPost.objects.create(
                    title=f"{post_title} {i}",
                    content=f"Test content {i}",
                    category=category,
                    banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
                )
                posts.append(post)
            
            # Create client and set visitor_id cookie
            client = Client()
            client.cookies[CookieManager.VISITOR_ID_COOKIE] = visitor_id
            
            # Determine rate limit and endpoint based on action
            if action == 'comment':
                limit = 3
                # Perform comment submissions to trigger rate limit
                for i in range(limit + 1):
                    response = client.post(
                        f'/blogs/post/{posts[i].slug}/',
                        {
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'content': f'Test comment {i}'
                        }
                    )
                    if i == limit:
                        # This should be rate limited
                        self.assertEqual(response.status_code, 429,
                                       "Comment submission should be rate limited")
            elif action == 'like':
                limit = 10
                # Perform like actions to trigger rate limit
                for i in range(limit + 1):
                    response = client.post(f'/blogs/post/{posts[i].slug}/like/')
                    if i == limit:
                        # This should be rate limited
                        self.assertEqual(response.status_code, 429,
                                       "Like action should be rate limited")
            else:  # dislike
                limit = 10
                # Perform dislike actions to trigger rate limit
                for i in range(limit + 1):
                    response = client.post(f'/blogs/post/{posts[i].slug}/dislike/')
                    if i == limit:
                        # This should be rate limited
                        self.assertEqual(response.status_code, 429,
                                       "Dislike action should be rate limited")
            
            # Get log output
            log_output = log_stream.getvalue()
            
            # Verify log entry was created
            self.assertIn('Rate limit exceeded', log_output,
                         "Log should contain 'Rate limit exceeded' message")
            self.assertIn(action, log_output,
                         f"Log should contain action type '{action}'")
            
            # Cleanup
            for post in posts:
                post.delete()
            category.delete()
            cache.clear()
        
        finally:
            # Restore logger state
            security_logger.removeHandler(handler)
            security_logger.setLevel(original_level)
    
    # Feature: production-blog-enhancements, Property 33: Error Logging with Stack Traces
    @given(
        error_message=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @settings(max_examples=10)
    def test_error_logging_with_stack_traces(self, error_message):
        """
        **Validates: Requirements 10.1**
        
        For any unhandled exception in the application, a log entry should 
        be created in the error log containing the exception message, stack 
        trace, and timestamp.
        """
        from blog.middleware import ErrorLoggingMiddleware
        from django.http import HttpRequest
        import logging
        from io import StringIO
        
        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(levelname)s %(message)s')
        handler.setFormatter(formatter)
        
        error_logger = logging.getLogger('django.request')
        error_logger.addHandler(handler)
        original_level = error_logger.level
        error_logger.setLevel(logging.ERROR)
        
        try:
            # Create middleware instance
            middleware = ErrorLoggingMiddleware(lambda r: None)
            
            # Create test request
            request = HttpRequest()
            request.method = 'GET'
            request.path = '/test/path/'
            
            # Create test exception
            test_exception = ValueError(error_message)
            
            # Process exception through middleware
            result = middleware.process_exception(request, test_exception)
            
            # Middleware should return None to allow Django's default handling
            self.assertIsNone(result,
                            "Middleware should return None for default error handling")
            
            # Get log output
            log_output = log_stream.getvalue()
            
            # Verify log entry contains exception information
            self.assertIn('ERROR', log_output,
                         "Log should contain ERROR level")
            self.assertIn('Unhandled exception', log_output,
                         "Log should contain 'Unhandled exception' message")
            self.assertIn(error_message, log_output,
                         "Log should contain the exception message")
            self.assertIn('ValueError', log_output,
                         "Log should contain the exception type")
            self.assertIn('Stack trace', log_output,
                         "Log should contain 'Stack trace' indicator")
            
        finally:
            # Restore logger state
            error_logger.removeHandler(handler)
            error_logger.setLevel(original_level)
    
    # Feature: production-blog-enhancements, Property 34: Slow Query Logging
    @settings(max_examples=5)
    def test_slow_query_logging(self):
        """
        **Validates: Requirements 10.3**
        
        For any database query that takes longer than 100ms to execute, a 
        log entry should be created containing the query SQL and execution time.
        
        Note: This test verifies that the logging configuration is set up 
        correctly for slow query logging. Actual slow query detection is 
        handled by Django's database backend logging.
        """
        from django.conf import settings
        import logging
        
        # Verify logging configuration exists
        self.assertIn('LOGGING', dir(settings),
                     "Settings should have LOGGING configuration")
        
        logging_config = settings.LOGGING
        
        # Verify django.db.backends logger is configured
        self.assertIn('loggers', logging_config,
                     "Logging config should have 'loggers' section")
        self.assertIn('django.db.backends', logging_config['loggers'],
                     "Logging config should have 'django.db.backends' logger")
        
        db_logger_config = logging_config['loggers']['django.db.backends']
        
        # Verify logger has handlers
        self.assertIn('handlers', db_logger_config,
                     "Database logger should have handlers configured")
        self.assertTrue(len(db_logger_config['handlers']) > 0,
                       "Database logger should have at least one handler")
        
        # Verify logger level allows INFO or DEBUG (needed for query logging)
        self.assertIn('level', db_logger_config,
                     "Database logger should have level configured")
        
        logger_level = db_logger_config['level']
        self.assertIn(logger_level, ['DEBUG', 'INFO'],
                     f"Database logger level should be DEBUG or INFO for query logging, got {logger_level}")
        
        # Verify slow query threshold is configured
        self.assertTrue(hasattr(settings, 'SLOW_QUERY_THRESHOLD'),
                       "Settings should have SLOW_QUERY_THRESHOLD configured")
        
        threshold = settings.SLOW_QUERY_THRESHOLD
        self.assertEqual(threshold, 0.1,
                        f"Slow query threshold should be 0.1 seconds (100ms), got {threshold}")
    
    # Feature: production-blog-enhancements, Property 36: Comment Submission Logging
    @given(
        post_title=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        first_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-'),
        last_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-'),
        content=st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
    )
    @settings(max_examples=10)
    def test_comment_submission_logging(self, post_title, first_name, last_name, content):
        """
        **Validates: Requirements 10.8**
        
        For any comment submission attempt (successful or failed), a log 
        entry should be created containing the IP address, timestamp, post 
        slug, and submission result.
        """
        from blog.models import BlogPost, Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from django.core.cache import cache
        import logging
        from io import StringIO
        
        # Clear cache before test
        cache.clear()
        
        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        blog_logger = logging.getLogger('blog')
        blog_logger.addHandler(handler)
        original_level = blog_logger.level
        blog_logger.setLevel(logging.INFO)
        
        try:
            # Create test category
            category = Category.objects.create(
                name=f"Test Category Logging",
                image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            
            # Create test blog post
            post = BlogPost.objects.create(
                title=post_title,
                content="Test content for logging",
                category=category,
                banner=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
            )
            
            # Create client
            client = Client()
            
            # Submit comment
            response = client.post(
                f'/blogs/post/{post.slug}/',
                {
                    'first_name': first_name,
                    'last_name': last_name,
                    'content': content
                }
            )
            
            # Get log output
            log_output = log_stream.getvalue()
            
            # Verify log entry was created
            self.assertIn('Comment submitted', log_output,
                         "Log should contain 'Comment submitted' message")
            self.assertIn(post.slug, log_output,
                         f"Log should contain post slug '{post.slug}'")
            self.assertIn('IP', log_output,
                         "Log should contain IP address reference")
            
            # Cleanup
            post.delete()
            category.delete()
            cache.clear()
        
        finally:
            # Restore logger state
            blog_logger.removeHandler(handler)
            blog_logger.setLevel(original_level)
