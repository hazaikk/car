import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

from crawler.models import CarModel, UsedCar
from django.db.models import Count

print("Testing Car Models Availability")
print("=" * 40)

# Test total car models
total_models = CarModel.objects.count()
print(f"Total car models in database: {total_models}")

# Test car models with any used car data
models_with_data = CarModel.objects.annotate(
    used_cars_count=Count('usedcar')
).filter(
    used_cars_count__gt=0
).count()
print(f"Car models with used car data: {models_with_data}")

# Show first 10 car models with data
print("\nFirst 10 car models with data:")
models = CarModel.objects.annotate(
    used_cars_count=Count('usedcar')
).filter(
    used_cars_count__gt=0
).select_related('brand')[:10]

for model in models:
    print(f"  {model.brand.name} {model.name}: {model.used_cars_count} records")

print("\nTest completed!")