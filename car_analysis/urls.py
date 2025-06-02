from django.urls import path, include
from . import views

app_name = 'car_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('comparison/', views.comparison, name='comparison'),
    path('comparison/data/', views.comparison_data, name='comparison_data'),
    path('sales/<int:car_id>/', views.sales_prediction, name='sales_prediction'),
    path('price/<int:car_id>/', views.price_analysis, name='price_analysis'),
    path('market/', views.market_analysis, name='market_analysis'),
    
    # 数据分析功能 - 包含data_analysis应用的URL配置
    path('data/', include('data_analysis.urls')),
]