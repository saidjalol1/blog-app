from django.shortcuts import render
from django.views import View

class AboutPage(View):
    def get(self, request):
        return render(request, 'about.html')

    def post(self, request):
        # Handle POST request if needed
        return render(request, 'about.html')