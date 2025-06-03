#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test comparison analysis API functionality
"""

import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth.models import User

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import CarModel, UsedCar

def test_comparison_api():
    """Test comparison analysis API"""
    print("=== Testing Comparison Analysis API ===")
    
    # Create test client
    client = Client()
    
    # Create test user and login
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # Login
    client.login(username='testuser', password='testpass123')
    
    # Get car models with data
    car_models_with_data = []
    for car in CarModel.objects.all()[:10]:
        used_car_count = UsedCar.objects.filter(
            car_model=car,
            price__isnull=False,
            price__gt=0
        ).count()
        if used_car_count > 0:
            car_models_with_data.append({
                'id': car.id,
                'name': f"{car.brand.name} {car.name}",
                'count': used_car_count
            })
        if len(car_models_with_data) >= 3:
            break
    
    print(f"Found {len(car_models_with_data)} car models with data:")
    for car in car_models_with_data:
        print(f"  ID {car['id']}: {car['name']} ({car['count']} records)")
    
    if len(car_models_with_data) < 2:
        print("Error: Need at least 2 car models with data for comparison")
        return
    
    # Test comparison API
    test_car_ids = [car['id'] for car in car_models_with_data[:3]]
    print(f"\nTesting car IDs: {test_car_ids}")
    
    # Send POST request
    response = client.post(
        '/car_analysis/comparison/data/',
        data=json.dumps({'car_ids': test_car_ids}),
        content_type='application/json'
    )
    
    print(f"\nResponse status code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response success: {data.get('success', False)}")
            
            if data.get('success'):
                cars = data.get('cars', [])
                print(f"Returned car models count: {len(cars)}")
                
                for i, car in enumerate(cars):
                    print(f"\nCar Model {i+1}: {car.get('name')}")
                    print(f"  Average price: {car.get('price')}")
                    print(f"  Sales volume: {car.get('sales_volume')}")
                    print(f"  Fuel type: {car.get('fuel_type')}")
                    print(f"  Gearbox: {car.get('gearbox')}")
                    print(f"  Average mileage: {car.get('avg_mileage')}")
                    print(f"  Average age: {car.get('avg_year')}")
                    
                    performance = car.get('performance', {})
                    print(f"  Performance scores: Power {performance.get('power')}, Handling {performance.get('handling')}, Comfort {performance.get('comfort')}")
                    
                    ratings = car.get('ratings', {})
                    print(f"  User ratings: Overall {ratings.get('overall')}, Appearance {ratings.get('appearance')}, Interior {ratings.get('interior')}")
                    
                    data_quality = car.get('data_quality', {})
                    print(f"  Data quality: Total records {data_quality.get('total_records')}, Price records {data_quality.get('price_records')}")
            else:
                print(f"API returned error: {data.get('error')}")
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {response.content.decode()}")
    else:
        print(f"Request failed, status code: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

if __name__ == '__main__':
    test_comparison_api()