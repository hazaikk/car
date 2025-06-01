from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('price/', views.price_analysis, name='price_analysis'),
    path('brand/', views.brand_analysis, name='brand_analysis'),
    path('region/', views.region_analysis, name='region_analysis'),
    path('vehicle/', views.vehicle_attribute_analysis, name='vehicle_attribute_analysis'),
    path('api/data/', views.analysis_data_api, name='analysis_data_api'),
    path('interactive/', views.interactive_analysis, name='interactive_analysis'),
    path('export/', views.export_analysis, name='export_analysis'),
]