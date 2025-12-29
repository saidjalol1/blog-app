from django.shortcuts import render
from django.views import View


class HomePage(View):
    def get(self, request):
        return render(request, 'index.html')

    def post(self, request):
        # Handle POST request if needed
        return render(request, 'index.html')

    