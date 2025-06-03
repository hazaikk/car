#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import UsedCar
from django.db.models import Count, Min, Max

print("=== 数据库数据检查 ===")

# 检查总数据量
total_cars = UsedCar.objects.count()
print(f"总车辆数量: {total_cars}")

# 检查有价格的数据
valid_price_cars = UsedCar.objects.exclude(price__isnull=True).exclude(price__lte=0).count()
print(f"有效价格数据: {valid_price_cars}")

# 检查有上牌日期的数据
valid_date_cars = UsedCar.objects.exclude(registration_date__isnull=True).count()
print(f"有上牌日期数据: {valid_date_cars}")

# 检查同时有价格和上牌日期的数据
valid_both = UsedCar.objects.exclude(price__isnull=True).exclude(price__lte=0).exclude(registration_date__isnull=True).count()
print(f"同时有价格和上牌日期: {valid_both}")

# 检查上牌日期范围
if valid_date_cars > 0:
    date_range = UsedCar.objects.exclude(registration_date__isnull=True).aggregate(
        min_date=Min('registration_date'),
        max_date=Max('registration_date')
    )
    print(f"上牌日期范围: {date_range['min_date']} 到 {date_range['max_date']}")

# 检查价格范围
if valid_price_cars > 0:
    price_range = UsedCar.objects.exclude(price__isnull=True).exclude(price__lte=0).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    print(f"价格范围: {price_range['min_price']} 到 {price_range['max_price']} 万元")

# 检查品牌分布
brand_count = UsedCar.objects.values('car_model__brand__name').annotate(count=Count('id')).order_by('-count')[:5]
print("\n前5个品牌分布:")
for item in brand_count:
    print(f"  {item['car_model__brand__name']}: {item['count']}")

print("\n=== 检查完成 ===")