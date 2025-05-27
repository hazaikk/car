# data_analysis/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum, Min, Max
from crawler.models import Brand, CarModel, UsedCar
import pandas as pd
import numpy as np

def brand_analysis(request):
    """品牌分析"""
    # 获取品牌及其车辆数量
    brands = Brand.objects.annotate(
        car_count=Count('car_models__used_cars'),
        avg_price=Avg('car_models__used_cars__price')
    ).order_by('-car_count')[:10]
    
    context = {
        'brands': brands
    }
    return render(request, 'data_analysis/brand_analysis.html', context)

def price_trend_analysis(request):
    """价格趋势分析"""
    # 按年份统计平均价格
    price_trend = UsedCar.objects.values('year').annotate(
        avg_price=Avg('price'),
        count=Count('id')
    ).order_by('year')
    
    context = {
        'price_trend': price_trend
    }
    return render(request, 'data_analysis/price_trend.html', context)

def region_distribution(request):
    """地区分布分析"""
    # 按地区统计车辆数量
    regions = UsedCar.objects.values('location').annotate(
        count=Count('id'),
        avg_price=Avg('price')
    ).order_by('-count')[:20]
    
    context = {
        'regions': regions
    }
    return render(request, 'data_analysis/region_distribution.html', context)


def index(request):
    """数据分析首页"""
    # 获取基础统计数据
    total_cars = UsedCar.objects.count()
    total_brands = Brand.objects.count()
    avg_price = UsedCar.objects.aggregate(avg_price=Avg('price'))['avg_price']
    
    context = {
        'total_cars': total_cars,
        'total_brands': total_brands,
        'avg_price': avg_price,
    }
    return render(request, 'data_analysis/index.html', context)