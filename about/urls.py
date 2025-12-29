from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    path('', views.AboutPage.as_view(), name='about_page'),
]