from django.urls import path
from . import views

app_name = 'car_api'

urlpatterns = [
    path('docs/', views.api_docs, name='docs'),
] 