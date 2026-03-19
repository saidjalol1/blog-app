from django.urls import path
from . import views
from .health import health_check

app_name = 'blog'


urlpatterns = [
    path('', views.blog_page, name='blog_page'),
    path('fetch_blogs/', views.fetch_blogs, name='fetch_blogs'),
    path('filters/', views.fetch_filters, name='fetch_filters'),
    path('post/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),
    path('post/<slug:slug>/json/', views.blog_post_json, name='blog_post_json'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    path('post/<slug:slug>/dislike/', views.dislike_post, name='dislike_post'),
    path('health/', health_check, name='health_check'),
]