from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from crawler.models import Brand, CarModel, UsedCar
from django.db.models import Avg, Count, Sum, Min, Max
import json
def index(request):
    """首页"""
    # 统计数据
    total_cars = UsedCar.objects.count()
    total_brands = Brand.objects.count()
    avg_price = UsedCar.objects.all().aggregate(Avg('price'))['price__avg'] or 0
    
    # 最新数据
    latest_cars = UsedCar.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_cars': total_cars,
        'total_brands': total_brands,
        'avg_price': avg_price,
        'latest_cars': latest_cars,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def dashboard(request):
    """仪表盘"""
    # 这里可以添加更多的统计数据和图表
    return render(request, 'dashboard/dashboard.html')
# dashboard/views.py中添加


def car_price_chart(request):
    """车辆价格分布图表"""
    # 按价格区间统计车辆数量
    price_ranges = [
        {'min': 0, 'max': 5, 'label': '0-5万'},
        {'min': 5, 'max': 10, 'label': '5-10万'},
        {'min': 10, 'max': 15, 'label': '10-15万'},
        {'min': 15, 'max': 20, 'label': '15-20万'},
        {'min': 20, 'max': 30, 'label': '20-30万'},
        {'min': 30, 'max': 50, 'label': '30-50万'},
        {'min': 50, 'max': 100, 'label': '50-100万'},
        {'min': 100, 'max': 1000, 'label': '100万以上'},
    ]
    
    data = []
    for range_info in price_ranges:
        count = UsedCar.objects.filter(
            price__gte=range_info['min'],
            price__lt=range_info['max']
        ).count()
        data.append({
            'label': range_info['label'],
            'count': count
        })
    
    # 返回JSON数据供前端图表使用
    return JsonResponse({
        'labels': [item['label'] for item in data],
        'data': [item['count'] for item in data]
    })