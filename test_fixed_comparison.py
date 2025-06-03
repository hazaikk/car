import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import CarModel, UsedCar
from django.db.models import Q, Count

print("Testing Fixed Comparison Analysis")
print("=" * 50)

# 测试API接口返回的车型数据
print("\n1. Testing CarModel API with valid data filter:")
valid_car_models = CarModel.objects.annotate(
    valid_used_cars_count=Count(
        'usedcar',
        filter=Q(
            usedcar__price__isnull=False,
            usedcar__price__gt=0
        ) & ~Q(
            usedcar__title__isnull=True
        ) & ~Q(
            usedcar__title__exact=''
        )
    )
).filter(
    valid_used_cars_count__gt=0
).select_related('brand').order_by('brand__name', 'name')[:10]

print(f"Found {valid_car_models.count()} car models with valid data:")
for car in valid_car_models:
    valid_count = UsedCar.objects.filter(
        car_model=car,
        price__isnull=False,
        price__gt=0
    ).exclude(
        Q(title__isnull=True) | Q(title__exact='') |
        Q(price__lt=1) | Q(price__gt=1000)
    ).count()
    print(f"  {car.brand.name} {car.name}: {valid_count} valid records")

# 测试对比分析API
print("\n2. Testing Comparison Analysis API:")
client = Client()

try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

client.login(username='testuser', password='testpass123')

# 选择前3个有效车型进行测试
test_car_ids = [car.id for car in valid_car_models[:3]]
print(f"Testing with car IDs: {test_car_ids}")

# 获取CSRF token
csrf_response = client.get('/car_analysis/comparison/')
csrf_token = csrf_response.cookies.get('csrftoken')

response = client.post(
    '/car_analysis/comparison/data/',
    data=json.dumps({'car_ids': test_car_ids}),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else ''
)

print(f"Response status code: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"Response success: {data.get('success', False)}")
        
        if data.get('success'):
            cars = data.get('cars', [])
            print(f"Returned {len(cars)} car models for comparison")
            
            for i, car in enumerate(cars):
                print(f"\nCar {i+1}: {car.get('name')}")
                print(f"  Average price: {car.get('price')}")
                print(f"  Sales volume: {car.get('sales_volume')}")
                print(f"  Fuel type: {car.get('fuel_type')}")
                print(f"  Gearbox: {car.get('gearbox')}")
                print(f"  Average mileage: {car.get('avg_mileage')}")
                print(f"  Average age: {car.get('avg_year')}")
                
                performance = car.get('performance', {})
                if performance:
                    print(f"  Performance scores: Power={performance.get('power')}, Handling={performance.get('handling')}, Comfort={performance.get('comfort')}")
                
                ratings = car.get('ratings', {})
                if ratings:
                    print(f"  User ratings: Overall={ratings.get('overall')}, Appearance={ratings.get('appearance')}, Interior={ratings.get('interior')}")
                
                data_quality = car.get('data_quality', {})
                if data_quality:
                    print(f"  Data quality: Total={data_quality.get('total_records')}, Price={data_quality.get('price_records')}")
        else:
            print(f"API returned error: {data.get('error')}")
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.content.decode()}")
else:
    print(f"Request failed, status code: {response.status_code}")
    print(f"Response content: {response.content.decode()}")

print("\n" + "=" * 50)
print("Test completed!")