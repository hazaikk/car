from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('brand/', views.brand_analysis, name='brand_analysis'),
    path('price-trend/', views.price_trend_analysis, name='price_trend_analysis'),
    path('region/', views.region_distribution, name='region_distribution'),
]