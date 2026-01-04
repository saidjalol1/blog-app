Changelog: Home/Blog SEO & Loading Improvements

Summary
- Added `is_featured` boolean to `BlogPost` and migration `0005_add_featured_field.py`.
- Home page now server-renders `featured_posts` and `latest_posts` for SEO and faster first paint.
- Blog list page server-renders first page as `initial_posts` (improves SEO and works without JS).
- Added meta tags, Open Graph, Twitter card, and JSON-LD for article pages (`blog-detail`) and the home page.
- Added canonical links and improved JSON responses (added `description` and `canonical` to `blog_post_json`).
- Images are lazy-loaded (`loading="lazy"`, `decoding="async"`) both server-side and client-side.
- Conditional WhiteNoise integration for static compression (gzip/brotli) in production; safe if WhiteNoise is not installed in dev/testing.
- Added tests for home and blog endpoints and made test assertions for SEO meta tags.

How to apply changes locally
1. Install new requirement (optional for production features):
   pip install -r requirements.txt
2. Run migrations:
   python manage.py migrate
3. Run tests:
   python manage.py test
4. For production, run collectstatic and ensure WhiteNoise is present:
   pip install whitenoise
   python manage.py collectstatic

Notes & next steps
- Consider adding an `author` field on `BlogPost` for richer author metadata.
- Consider integrating an image pipeline (e.g., Thumbnail, Cloudinary) to generate responsive `srcset` and smaller images for better LCP.
- Add caching headers and CDN configuration for static/media in production.
