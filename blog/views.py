from django.shortcuts import render
from django.views import View

class BlogPage(View):
    def get(self, request):
        return render(request, 'blog.html')

    def post(self, request):
        # Handle POST request if needed
        return render(request, 'blog.html') 
    
