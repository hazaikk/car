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
from django.shortcuts import render

# 添加新页面的视图函数
def help_view(request):
    return render(request, 'help.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),  # allauth URLs
    path('accounts/', include('accounts.urls')),  # 用户账户管理
    path('', include('dashboard.urls')),  # 首页和仪表盘
    path('analysis/', include('data_analysis.urls')),  # 数据分析
    path('api/', include('api.urls')),  # API接口
    path('crawler/', include('crawler.urls')),  # 爬虫管理
    path('visualization/', include('visualization.urls')),  # 数据可视化
    path('car_analysis/', include('car_analysis.urls')),  # 汽车分析
    path('car_api/', include('car_api.urls')),  # 汽车API
    # 新增页面路由
    path('help/', help_view, name='help'),  # 使用帮助
    path('about/', about_view, name='about'),  # 关于我们
    path('contact/', contact_view, name='contact'),  # 联系我们
]

# 在开发环境中提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
