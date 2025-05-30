"""
URL configuration for cardata_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),  # allauth URLs
    path('accounts/', include('accounts.urls')),  # 自定义账户URLs
    path('', include('dashboard.urls')),  # 首页和仪表盘
    path('analysis/', include('data_analysis.urls')),  # 数据分析
    path('api/', include('api.urls')),  # API接口
    path('crawler/', include('crawler.urls')),  # 爬虫管理
    path('visualization/', include('visualization.urls')),  # 数据可视化
    path('car-analysis/', include('car_analysis.urls')),  # 智能分析
    path('car-api/', include('car_api.urls')),  # API文档
]

# 在开发环境中提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
