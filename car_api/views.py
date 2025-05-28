from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def api_docs(request):
    """API文档页面"""
    return render(request, 'car_api/docs.html')
