from django.contrib import admin

# Register your models here.
# crawler/admin.py
from django.contrib import admin
from .models import Brand, CarModel, UsedCar

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    list_filter = ('brand',)
    search_fields = ('name', 'brand__name')

@admin.register(UsedCar)
class UsedCarAdmin(admin.ModelAdmin):
    list_display = ('title', 'car_model', 'price', 'year', 'mileage', 'location')
    list_filter = ('car_model__brand', 'year', 'location')
    search_fields = ('title', 'car_model__name', 'car_model__brand__name')
    date_hierarchy = 'created_at'