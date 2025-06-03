from django.shortcuts import render
# api/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from crawler.models import Brand, CarModel, UsedCar
from .serializers import BrandSerializer, CarModelSerializer, UsedCarSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q, Count

class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class CarModelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CarModelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['brand']
    search_fields = ['name']
    pagination_class = None  # 禁用分页，返回所有车型
    
    def get_queryset(self):
        """返回所有车型，让用户可以选择任意车型进行对比"""
        return CarModel.objects.select_related('brand').order_by('brand__name', 'name')

class UsedCarViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsedCar.objects.all()
    serializer_class = UsedCarSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['car_model__brand', 'year', 'location']
    search_fields = ['title', 'car_model__name', 'car_model__brand__name']
    ordering_fields = ['price', 'year', 'mileage', 'created_at']


@api_view(['GET'])
def index(request):
    """API首页"""
    return Response({
        'message': '欢迎使用汽车之家数据可视化与智能分析平台API',
        'endpoints': {
            'brands': '/api/brands/',
            'car_models': '/api/car-models/',
            'used_cars': '/api/used-cars/'
        }
    })