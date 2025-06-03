from django.urls import path
from . import views

app_name = 'visualization'

urlpatterns = [
    # 图表相关
    path('charts/', views.chart_list, name='chart_list'),
    path('charts/my/', views.my_charts, name='my_charts'),
    path('charts/create/', views.quick_chart, name='chart_create'),
    path('charts/<int:chart_id>/', views.chart_detail, name='chart_detail'),
    path('charts/<int:chart_id>/edit/', views.chart_edit, name='chart_edit'),
    path('charts/<int:chart_id>/data/', views.chart_data, name='chart_data'),
    path('charts/<int:chart_id>/preview/', views.chart_preview, name='chart_preview'),
    path('charts/delete/', views.chart_delete, name='chart_delete'),
    
    # 仪表盘相关

    
    # API相关
    path('api/filter-options/', views.get_filter_options, name='get_filter_options'),
]