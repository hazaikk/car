#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的对比分析功能
"""

import os
import sys
import json

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User

from crawler.models import CarModel, UsedCar

def test_comparison_fix():
    """测试修复后的对比分析功能"""
    print("=== 测试修复后的对比分析功能 ===")
    
    # 1. 检查车型数据可用性
    print("\n1. 检查车型数据可用性:")
    total_models = CarModel.objects.count()
    models_with_data = CarModel.objects.filter(usedcar__isnull=False).distinct().count()
    print(f"总车型数量: {total_models}")
    print(f"有二手车数据的车型数量: {models_with_data}")
    
    # 获取前10个有数据的车型
    models_with_data_list = CarModel.objects.filter(
        usedcar__isnull=False
    ).distinct()[:10]
    
    print("\n前10个有数据的车型:")
    for model in models_with_data_list:
        used_car_count = UsedCar.objects.filter(car_model=model).count()
        print(f"- {model.brand.name} {model.name}: {used_car_count}条记录")
    
    # 2. 测试API端点
    print("\n2. 测试车型API端点:")
    client = Client()
    
    # 创建测试用户并登录
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    client.login(username='testuser', password='testpass123')
    
    # 测试车型列表API
    response = client.get('/api/car-models/')
    print(f"车型API状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            car_models = data['results']
        else:
            car_models = data
        print(f"API返回车型数量: {len(car_models)}")
        
        if len(car_models) >= 3:
            # 选择前3个车型进行对比测试
            selected_ids = [car['id'] for car in car_models[:3]]
            print(f"选择的车型ID: {selected_ids}")
            
            # 3. 测试对比分析API
            print("\n3. 测试对比分析API:")
            
            # 获取CSRF token
            csrf_response = client.get('/car_analysis/comparison/')
            csrf_token = csrf_response.cookies.get('csrftoken')
            
            if csrf_token:
                csrf_token = csrf_token.value
            
            # 测试对比API
            comparison_response = client.post(
                '/car_analysis/comparison/data/',
                data=json.dumps({'car_ids': selected_ids}),
                content_type='application/json',
                HTTP_X_CSRFTOKEN=csrf_token
            )
            
            print(f"对比API状态码: {comparison_response.status_code}")
            
            if comparison_response.status_code == 200:
                comparison_data = comparison_response.json()
                print(f"对比API响应: {comparison_data.get('success', False)}")
                
                if comparison_data.get('success'):
                    cars = comparison_data.get('cars', [])
                    print(f"返回的车型数量: {len(cars)}")
                    
                    for i, car in enumerate(cars):
                        print(f"\n车型 {i+1}: {car.get('name', 'Unknown')}")
                        print(f"  - 价格: {car.get('price', 'N/A')}")
                        print(f"  - 在售数量: {car.get('sales_volume', 'N/A')}")
                        print(f"  - 燃料类型: {car.get('fuel_type', 'N/A')}")
                        print(f"  - 变速箱: {car.get('gearbox', 'N/A')}")
                        
                        # 检查性能数据
                        performance = car.get('performance', {})
                        if performance:
                            print(f"  - 性能评分: 动力{performance.get('power', 0)}, 操控{performance.get('handling', 0)}")
                        
                        # 检查评分数据
                        ratings = car.get('ratings', {})
                        if ratings:
                            print(f"  - 用户评分: 综合{ratings.get('overall', 0)}, 外观{ratings.get('appearance', 0)}")
                else:
                    print(f"对比失败: {comparison_data.get('error', 'Unknown error')}")
            else:
                print(f"对比API请求失败: {comparison_response.content.decode()}")
        else:
            print("可用车型数量不足，无法进行对比测试")
    else:
        print(f"车型API请求失败: {response.content.decode()}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_comparison_fix()