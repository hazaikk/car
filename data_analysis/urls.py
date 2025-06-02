from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('price/', views.price_analysis, name='price_analysis'),
    path('price/data/', views.price_analysis_data, name='price_analysis_data'),
    path('region/', views.region_analysis, name='region_analysis'),
    path('region/data/', views.region_analysis_data, name='region_analysis_data'),
    path('api/data/', views.analysis_data_api, name='analysis_data_api'),
    path('api/filter-options/', views.get_filter_options, name='get_filter_options'),
    path('interactive/', views.interactive_analysis, name='interactive_analysis'),
    path('interactive/data/', views.interactive_analysis_data, name='interactive_analysis_data'),
    path('export/', views.export_analysis, name='export_analysis'),
]