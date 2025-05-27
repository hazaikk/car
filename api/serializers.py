# api/serializers.py
from rest_framework import serializers
from crawler.models import Brand, CarModel, UsedCar

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class CarModelSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    
    class Meta:
        model = CarModel
        fields = '__all__'

class UsedCarSerializer(serializers.ModelSerializer):
    car_model = CarModelSerializer(read_only=True)
    
    class Meta:
        model = UsedCar
        fields = '__all__'