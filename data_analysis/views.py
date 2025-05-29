# data_analysis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum, Min, Max
from django.contrib.auth.decorators import login_required
from crawler.models import Brand, CarModel, UsedCar
from .models import PriceAnalysisResult, BrandAnalysisResult, RegionAnalysisResult, VehicleAttributeAnalysisResult
from .services import PriceAnalysisService, BrandAnalysisService, RegionAnalysisService, VehicleAttributeAnalysisService
import pandas as pd
import numpy as np
import json
from django.utils import timezone

@login_required
def index(request):
    """数据分析首页"""
    # 获取基础统计数据
    total_cars = UsedCar.objects.count()
    total_brands = Brand.objects.count()
    avg_price = UsedCar.objects.aggregate(avg_price=Avg('price'))['avg_price']
    
    # 自动生成分析结果（如果不存在）
    today = timezone.now().date()
    
    # 价格分析
    price_analysis, price_created = PriceAnalysisResult.objects.get_or_create(
        analysis_type='brand_price',
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    if price_created:
        result_data, summary = PriceAnalysisService.analyze_brand_price()
        price_analysis.result_data = result_data
        price_analysis.summary = summary
        price_analysis.save()
    
    # 品牌分析
    brand_analysis, brand_created = BrandAnalysisResult.objects.get_or_create(
        analysis_type='brand_popularity',
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    if brand_created:
        result_data, summary = BrandAnalysisService.analyze_brand_popularity()
        brand_analysis.result_data = result_data
        brand_analysis.summary = summary
        brand_analysis.save()
    
    # 地区分析
    region_analysis, region_created = RegionAnalysisResult.objects.get_or_create(
        analysis_type='region_car_count',
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    if region_created:
        result_data, summary = RegionAnalysisService.analyze_region_car_count()
        region_analysis.result_data = result_data
        region_analysis.summary = summary
        region_analysis.save()
    
    # 车辆属性分析
    vehicle_analysis, vehicle_created = VehicleAttributeAnalysisResult.objects.get_or_create(
        analysis_type='fuel_type',
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    if vehicle_created:
        result_data, summary = VehicleAttributeAnalysisService.analyze_fuel_type()
        vehicle_analysis.result_data = result_data
        vehicle_analysis.summary = summary
        vehicle_analysis.save()
    
    # 获取最新的分析结果
    latest_price_analysis = price_analysis
    latest_brand_analysis = brand_analysis
    latest_region_analysis = region_analysis
    latest_vehicle_analysis = vehicle_analysis
    
    context = {
        'total_cars': total_cars,
        'total_brands': total_brands,
        'avg_price': avg_price,
        'latest_price_analysis': latest_price_analysis,
        'latest_brand_analysis': latest_brand_analysis,
        'latest_region_analysis': latest_region_analysis,
        'latest_vehicle_analysis': latest_vehicle_analysis,
    }
    return render(request, 'data_analysis/index.html', context)

@login_required
def price_analysis(request):
    """价格分析页面"""
    analysis_type = request.GET.get('type', 'brand_price')
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # 获取或创建分析结果
    today = timezone.now().date()
    analysis, created = PriceAnalysisResult.objects.get_or_create(
        analysis_type=analysis_type,
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    
    # 如果是新创建的或需要刷新，则进行分析
    if created or refresh:
        if analysis_type == 'brand_price':
            result_data, summary = PriceAnalysisService.analyze_brand_price()
        elif analysis_type == 'region_price':
            result_data, summary = PriceAnalysisService.analyze_region_price()
        elif analysis_type == 'year_price':
            result_data, summary = PriceAnalysisService.analyze_year_price()
        elif analysis_type == 'mileage_price':
            result_data, summary = PriceAnalysisService.analyze_mileage_price()
        else:
            result_data, summary = {}, '未知的分析类型'
        
        analysis.result_data = result_data
        analysis.summary = summary
        analysis.save()
    
    context = {
        'analysis': analysis,
        'analysis_type': analysis_type,
        'analysis_types': dict(PriceAnalysisResult._meta.get_field('analysis_type').choices),
    }
    return render(request, 'data_analysis/price_analysis.html', context)

@login_required
def brand_analysis(request):
    """品牌分析页面"""
    analysis_type = request.GET.get('type', 'brand_popularity')
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # 获取或创建分析结果
    today = timezone.now().date()
    analysis, created = BrandAnalysisResult.objects.get_or_create(
        analysis_type=analysis_type,
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    
    # 如果是新创建的或需要刷新，则进行分析
    if created or refresh:
        if analysis_type == 'brand_popularity':
            result_data, summary = BrandAnalysisService.analyze_brand_popularity()
        elif analysis_type == 'brand_price_range':
            result_data, summary = BrandAnalysisService.analyze_brand_price_range()
        elif analysis_type == 'brand_region_distribution':
            result_data, summary = BrandAnalysisService.analyze_brand_region_distribution()
        else:
            result_data, summary = {}, '未知的分析类型'
        
        analysis.result_data = result_data
        analysis.summary = summary
        analysis.save()
    
    context = {
        'analysis': analysis,
        'analysis_type': analysis_type,
        'analysis_types': dict(BrandAnalysisResult._meta.get_field('analysis_type').choices),
    }
    return render(request, 'data_analysis/brand_analysis.html', context)

@login_required
def region_analysis(request):
    """地区分析页面"""
    analysis_type = request.GET.get('type', 'region_car_count')
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # 获取或创建分析结果
    today = timezone.now().date()
    analysis, created = RegionAnalysisResult.objects.get_or_create(
        analysis_type=analysis_type,
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    
    # 如果是新创建的或需要刷新，则进行分析
    if created or refresh:
        if analysis_type == 'region_car_count':
            result_data, summary = RegionAnalysisService.analyze_region_car_count()
        elif analysis_type == 'region_price_level':
            result_data, summary = RegionAnalysisService.analyze_region_price_level()
        elif analysis_type == 'region_brand_preference':
            result_data, summary = RegionAnalysisService.analyze_region_brand_preference()
        else:
            result_data, summary = {}, '未知的分析类型'
        
        analysis.result_data = result_data
        analysis.summary = summary
        analysis.save()
    
    context = {
        'analysis': analysis,
        'analysis_type': analysis_type,
        'analysis_types': dict(RegionAnalysisResult._meta.get_field('analysis_type').choices),
    }
    return render(request, 'data_analysis/region_analysis.html', context)

@login_required
def vehicle_attribute_analysis(request):
    """车辆属性分析页面"""
    analysis_type = request.GET.get('type', 'fuel_type_analysis')
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # 获取或创建分析结果
    today = timezone.now().date()
    analysis, created = VehicleAttributeAnalysisResult.objects.get_or_create(
        analysis_type=analysis_type,
        analysis_date=today,
        defaults={'result_data': {}, 'summary': ''}
    )
    
    # 如果是新创建的或需要刷新，则进行分析
    if created or refresh:
        if analysis_type == 'fuel_type_analysis':
            result_data, summary = VehicleAttributeAnalysisService.analyze_fuel_type()
        elif analysis_type == 'transmission_analysis':
            result_data, summary = VehicleAttributeAnalysisService.analyze_transmission()
        elif analysis_type == 'color_preference':
            result_data, summary = VehicleAttributeAnalysisService.analyze_color_preference()
        elif analysis_type == 'engine_type_analysis':
            result_data, summary = VehicleAttributeAnalysisService.analyze_engine_type()
        elif analysis_type == 'mileage_distribution':
            result_data, summary = VehicleAttributeAnalysisService.analyze_mileage_distribution()
        else:
            result_data, summary = {}, '未知的分析类型'
        
        analysis.result_data = result_data
        analysis.summary = summary
        analysis.save()
    
    context = {
        'analysis': analysis,
        'analysis_type': analysis_type,
        'analysis_types': dict(VehicleAttributeAnalysisResult._meta.get_field('analysis_type').choices),
    }
    return render(request, 'data_analysis/vehicle_attribute_analysis.html', context)

@login_required
def analysis_data_api(request):
    """分析数据API，用于前端AJAX请求"""
    analysis_model = request.GET.get('model')
    analysis_id = request.GET.get('id')
    
    if analysis_model == 'price':
        analysis = PriceAnalysisResult.objects.get(id=analysis_id)
    elif analysis_model == 'brand':
        analysis = BrandAnalysisResult.objects.get(id=analysis_id)
    elif analysis_model == 'region':
        analysis = RegionAnalysisResult.objects.get(id=analysis_id)
    elif analysis_model == 'vehicle':
        analysis = VehicleAttributeAnalysisResult.objects.get(id=analysis_id)
    else:
        return JsonResponse({'error': '未知的分析模型'}, status=400)
    
    return JsonResponse({
        'result_data': analysis.result_data,
        'summary': analysis.summary,
        'analysis_type': analysis.analysis_type,
        'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d'),
    })

@login_required
def interactive_analysis(request):
    """交互式数据分析页面"""
    # 获取可用的数据源
    brands = Brand.objects.all()
    regions = UsedCar.objects.values_list('location', flat=True).distinct()
    
    # 获取可用的分析类型
    price_analysis_types = dict(PriceAnalysisResult._meta.get_field('analysis_type').choices)
    brand_analysis_types = dict(BrandAnalysisResult._meta.get_field('analysis_type').choices)
    region_analysis_types = dict(RegionAnalysisResult._meta.get_field('analysis_type').choices)
    vehicle_analysis_types = dict(VehicleAttributeAnalysisResult._meta.get_field('analysis_type').choices)
    
    # 处理分析请求
    if request.method == 'POST':
        analysis_category = request.POST.get('analysis_category')
        analysis_type = request.POST.get('analysis_type')
        data_filter = request.POST.get('data_filter', '{}')
        
        try:
            data_filter = json.loads(data_filter)
        except json.JSONDecodeError:
            data_filter = {}
        
        # 根据选择的分析类型执行分析
        result_data = {}
        summary = ''
        
        if analysis_category == 'price':
            if analysis_type == 'brand_price':
                # 如果有品牌过滤
                if 'brands' in data_filter and data_filter['brands']:
                    # 这里需要修改服务类方法以支持过滤
                    # 简化示例：直接在这里实现过滤逻辑
                    brand_ids = [int(b) for b in data_filter['brands']]
                    brand_price_data = UsedCar.objects.filter(
                        car_model__brand__id__in=brand_ids
                    ).values(
                        'car_model__brand__name'
                    ).annotate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price'),
                        car_count=Count('id')
                    ).filter(car_count__gte=5).order_by('-avg_price')
                    
                    result_data = {
                        'brands': [item['car_model__brand__name'] for item in brand_price_data],
                        'avg_prices': [float(item['avg_price']) for item in brand_price_data],
                        'min_prices': [float(item['min_price']) for item in brand_price_data],
                        'max_prices': [float(item['max_price']) for item in brand_price_data],
                        'car_counts': [item['car_count'] for item in brand_price_data]
                    }
                    
                    top_brands = brand_price_data[:5]
                    if top_brands:
                        summary = f"价格最高的五个品牌是：{', '.join([item['car_model__brand__name'] for item in top_brands])}，"
                        summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_brands])}"
                    else:
                        summary = "没有符合条件的数据。"
                else:
                    # 如果没有过滤，使用原有服务方法
                    result_data, summary = PriceAnalysisService.analyze_brand_price()
            # 其他价格分析类型...
            elif analysis_type == 'region_price':
                if 'regions' in data_filter and data_filter['regions']:
                    regions = data_filter['regions']
                    region_price_data = UsedCar.objects.filter(
                        location__in=regions
                    ).values(
                        'location'
                    ).annotate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price'),
                        car_count=Count('id')
                    ).filter(car_count__gte=3).order_by('-avg_price')
                    
                    result_data = {
                        'regions': [item['location'] for item in region_price_data],
                        'avg_prices': [float(item['avg_price']) for item in region_price_data],
                        'min_prices': [float(item['min_price']) for item in region_price_data],
                        'max_prices': [float(item['max_price']) for item in region_price_data],
                        'car_counts': [item['car_count'] for item in region_price_data]
                    }
                    
                    top_regions = region_price_data[:5]
                    if top_regions:
                        summary = f"价格水平最高的五个地区是：{', '.join([item['location'] for item in top_regions])}，"
                        summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_regions])}"
                    else:
                        summary = "没有符合条件的数据。"
                else:
                    result_data, summary = PriceAnalysisService.analyze_region_price()
            else:
                # 其他价格分析类型使用原有服务方法
                if analysis_type == 'year_price':
                    result_data, summary = PriceAnalysisService.analyze_year_price()
                elif analysis_type == 'mileage_price':
                    result_data, summary = PriceAnalysisService.analyze_mileage_price()
        
        elif analysis_category == 'brand':
            # 品牌分析逻辑...
            if analysis_type in brand_analysis_types:
                if analysis_type == 'brand_popularity':
                    result_data, summary = BrandAnalysisService.analyze_brand_popularity()
                elif analysis_type == 'brand_price_range':
                    result_data, summary = BrandAnalysisService.analyze_brand_price_range()
                elif analysis_type == 'brand_region_distribution':
                    result_data, summary = BrandAnalysisService.analyze_brand_region_distribution()
        
        elif analysis_category == 'region':
            # 地区分析逻辑...
            if analysis_type in region_analysis_types:
                if analysis_type == 'region_car_count':
                    result_data, summary = RegionAnalysisService.analyze_region_car_count()
                elif analysis_type == 'region_price_level':
                    result_data, summary = RegionAnalysisService.analyze_region_price_level()
                elif analysis_type == 'region_brand_preference':
                    result_data, summary = RegionAnalysisService.analyze_region_brand_preference()
        
        elif analysis_category == 'vehicle':
            # 车辆属性分析逻辑...
            if analysis_type in vehicle_analysis_types:
                if analysis_type == 'fuel_type_analysis':
                    result_data, summary = VehicleAttributeAnalysisService.analyze_fuel_type()
                elif analysis_type == 'transmission_analysis':
                    result_data, summary = VehicleAttributeAnalysisService.analyze_transmission()
                elif analysis_type == 'color_preference':
                    result_data, summary = VehicleAttributeAnalysisService.analyze_color_preference()
                elif analysis_type == 'engine_type_analysis':
                    result_data, summary = VehicleAttributeAnalysisService.analyze_engine_type()
                elif analysis_type == 'mileage_distribution':
                    result_data, summary = VehicleAttributeAnalysisService.analyze_mileage_distribution()
        
        # 返回分析结果
        return JsonResponse({
            'result_data': result_data,
            'summary': summary,
            'analysis_type': analysis_type,
        })
    
    context = {
        'brands': brands,
        'regions': regions,
        'price_analysis_types': price_analysis_types,
        'brand_analysis_types': brand_analysis_types,
        'region_analysis_types': region_analysis_types,
        'vehicle_analysis_types': vehicle_analysis_types,
    }
    return render(request, 'data_analysis/interactive_analysis.html', context)