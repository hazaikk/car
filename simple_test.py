import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import CarModel, UsedCar

print("Testing Comparison Analysis API")

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
    sys.exit(1)

test_car_ids = [car['id'] for car in car_models_with_data[:3]]
print(f"Testing car IDs: {test_car_ids}")

# Get CSRF token first
csrf_response = client.get('/car_analysis/comparison/')
csrf_token = csrf_response.cookies.get('csrftoken')

headers = {
    'X-CSRFToken': csrf_token.value if csrf_token else '',
    'Content-Type': 'application/json'
}

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
            print(f"Returned car models count: {len(cars)}")
            
            for i, car in enumerate(cars):
                print(f"Car Model {i+1}: {car.get('name')}")
                print(f"  Average price: {car.get('price')}")
                print(f"  Sales volume: {car.get('sales_volume')}")
                print(f"  Fuel type: {car.get('fuel_type')}")
                print(f"  Gearbox: {car.get('gearbox')}")
        else:
            print(f"API returned error: {data.get('error')}")
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.content.decode()}")
else:
    print(f"Request failed, status code: {response.status_code}")
    print(f"Response content: {response.content.decode()}")