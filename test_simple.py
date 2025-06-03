#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试对比分析功能
"""

import os
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import CarModel, UsedCar
from django.db.models import Count

def test_simple():
    """简单测试"""
    print("=== 简单测试对比分析数据 ===")
    
    # 1. 检查车型数据
    print("\n1. 车型数据统计:")
    total_models = CarModel.objects.count()
    print(f"总车型数量: {total_models}")
    
    # 使用与API相同的查询逻辑
    models_with_data = CarModel.objects.annotate(
        used_cars_count=Count('usedcar')
    ).filter(
        used_cars_count__gt=0
    ).count()
    print(f"有二手车数据的车型数量: {models_with_data}")
    
    # 获取前5个有数据的车型
    models_list = CarModel.objects.annotate(
        used_cars_count=Count('usedcar')
    ).filter(
        used_cars_count__gt=0
    ).select_related('brand').order_by('brand__name', 'name')[:5]
    
    print("\n前5个有数据的车型:")
    for model in models_list:
        used_car_count = UsedCar.objects.filter(car_model=model).count()
        print(f"- ID: {model.id}, 名称: {model.brand.name} {model.name}, 记录数: {used_car_count}")
    
    # 2. 检查二手车数据质量
    print("\n2. 二手车数据质量检查:")
    total_used_cars = UsedCar.objects.count()
    valid_price_cars = UsedCar.objects.filter(
        price__isnull=False,
        price__gt=0,
        price__lt=1000
    ).count()
    
    print(f"总二手车记录数: {total_used_cars}")
    print(f"有效价格记录数: {valid_price_cars}")
    
    # 3. 模拟对比分析
    if len(models_list) >= 2:
        print("\n3. 模拟对比分析:")
        selected_models = models_list[:2]  # 选择前2个车型
        
        for model in selected_models:
            print(f"\n车型: {model.brand.name} {model.name}")
            
            # 获取该车型的有效二手车数据
            used_cars = UsedCar.objects.filter(
                car_model=model,
                price__isnull=False,
                price__gt=0,
                price__lt=1000
            )
            
            count = used_cars.count()
            if count > 0:
                avg_price = sum(car.price for car in used_cars) / count
                print(f"  - 有效记录数: {count}")
                print(f"  - 平均价格: {avg_price:.2f}万元")
                
                # 检查其他字段
                fuel_types = used_cars.exclude(
                    fuel_type__isnull=True
                ).exclude(
                    fuel_type__exact=''
                ).values_list('fuel_type', flat=True).distinct()
                
                if fuel_types:
                    print(f"  - 燃料类型: {', '.join(fuel_types)}")
                
                gearbox_types = used_cars.exclude(
                    gearbox__isnull=True
                ).exclude(
                    gearbox__exact=''
                ).values_list('gearbox', flat=True).distinct()
                
                if gearbox_types:
                    print(f"  - 变速箱类型: {', '.join(gearbox_types)}")
            else:
                print(f"  - 无有效数据")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_simple()