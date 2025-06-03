#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import UsedCar, CarModel

print(f'UsedCar总数: {UsedCar.objects.count()}')
print(f'CarModel总数: {CarModel.objects.count()}')

print('\n前5个CarModel:')
for car in CarModel.objects.all()[:5]:
    print(f'  {car.id}: {car.brand.name} {car.name}')

print('\n每个CarModel对应的UsedCar数量:')
for car in CarModel.objects.all()[:5]:
    used_car_count = UsedCar.objects.filter(car_model=car).count()
    print(f'  {car.brand.name} {car.name}: {used_car_count}条')

print("\n检查UsedCar数据样例:")
used_cars_sample = UsedCar.objects.all()[:5]
for car in used_cars_sample:
    print(f"  价格: {car.price}, 里程: {car.mileage}, 车型: {car.car_model.brand.name} {car.car_model.name}")

# 检查前端传递的具体car_ids是否存在
print("\n检查前端传递的car_ids:")
test_car_ids = ['6440', '6558', '6490']
for car_id in test_car_ids:
    try:
        car = CarModel.objects.get(id=car_id)
        used_car_count = UsedCar.objects.filter(car_model=car).count()
        print(f"  ID {car_id}: {car.brand.name} {car.name} - {used_car_count}条二手车")
    except CarModel.DoesNotExist:
        print(f"  ID {car_id}: 不存在")

# 显示实际存在的car_id范围
print("\n实际存在的CarModel ID范围:")
first_car = CarModel.objects.first()
last_car = CarModel.objects.last()
if first_car and last_car:
    print(f"  最小ID: {first_car.id}, 最大ID: {last_car.id}")
    print(f"  总数: {CarModel.objects.count()}")