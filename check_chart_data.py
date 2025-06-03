#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import UsedCar
from django.db.models import Count
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

print('=== 数据库数据分析 ===')
print(f'总车辆数: {UsedCar.objects.count()}')

# 检查数据的时间分布
print('\n=== 按月分布 ===')
monthly = UsedCar.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    count=Count('id')
).order_by('month')

for item in monthly[:10]:
    if item['month']:
        print(f"{item['month'].strftime('%Y-%m')}: {item['count']}辆")

# 检查最近的数据
print('\n=== 最近10条数据的创建时间 ===')
recent_cars = UsedCar.objects.order_by('-created_at')[:10]
for car in recent_cars:
    print(f"ID: {car.id}, 创建时间: {car.created_at}, 品牌: {car.car_model.brand.name if car.car_model and car.car_model.brand else '未知'}")

# 检查数据的时间范围
print('\n=== 数据时间范围 ===')
first_car = UsedCar.objects.order_by('created_at').first()
last_car = UsedCar.objects.order_by('-created_at').first()
if first_car and last_car:
    print(f"最早数据: {first_car.created_at}")
    print(f"最新数据: {last_car.created_at}")
    
# 检查品牌分布
print('\n=== 品牌分布 (前10) ===')
brand_stats = UsedCar.objects.values('car_model__brand__name').annotate(
    count=Count('id')
).order_by('-count')[:10]

for item in brand_stats:
    brand_name = item['car_model__brand__name'] or '未知品牌'
    print(f"{brand_name}: {item['count']}辆")