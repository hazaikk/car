# data_analysis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Avg, Count, Sum, Min, Max
from django.contrib.auth.decorators import login_required
from crawler.models import Brand, CarModel, UsedCar
from .models import PriceAnalysisResult, BrandAnalysisResult, RegionAnalysisResult, VehicleAttributeAnalysisResult
from .services import PriceAnalysisService, BrandAnalysisService, RegionAnalysisService, VehicleAttributeAnalysisService
import pandas as pd
import numpy as np
import json
import io
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

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
        
        # 应用过滤条件
        filters = request.POST.get('filters', '{}')
        try:
            filter_data = json.loads(filters)
        except json.JSONDecodeError:
            filter_data = {}
        
        # 构建查询条件
        query_filters = {}
        
        # 品牌过滤
        if 'brands' in filter_data and filter_data['brands']:
            query_filters['brand_id__in'] = filter_data['brands']
        
        # 地区过滤
        if 'regions' in filter_data and filter_data['regions']:
            query_filters['location__in'] = filter_data['regions']
        
        # 上牌日期过滤
        if 'date_from' in filter_data and filter_data['date_from']:
            query_filters['registration_date__gte'] = filter_data['date_from']
        if 'date_to' in filter_data and filter_data['date_to']:
            query_filters['registration_date__lte'] = filter_data['date_to']
        
        # 里程过滤
        if 'mileage_from' in filter_data and filter_data['mileage_from']:
            query_filters['mileage__gte'] = float(filter_data['mileage_from'])
        if 'mileage_to' in filter_data and filter_data['mileage_to']:
            query_filters['mileage__lte'] = float(filter_data['mileage_to'])
        
        # 价格过滤
        if 'price_from' in filter_data and filter_data['price_from']:
            query_filters['price__gte'] = float(filter_data['price_from'])
        if 'price_to' in filter_data and filter_data['price_to']:
            query_filters['price__lte'] = float(filter_data['price_to'])
        
        # 根据选择的分析类型执行分析
        result_data = {}
        summary = ''
        
        # 合并过滤条件
        if filter_data:
            data_filter.update(filter_data)
        
        if analysis_category == 'price':
            if analysis_type == 'brand_price':
                # 按品牌分析价格
                cars = UsedCar.objects.filter(**query_filters)
                brand_price_data = cars.values('car_model__brand__name').annotate(
                    avg_price=Avg('price'),
                    min_price=Min('price'),
                    max_price=Max('price'),
                    car_count=Count('id')
                ).filter(car_count__gte=3).order_by('-avg_price')
                
                result_data = {
                    'brands': [item['car_model__brand__name'] for item in brand_price_data],
                    'avg_prices': [float(item['avg_price']) for item in brand_price_data],
                    'min_prices': [float(item['min_price']) for item in brand_price_data],
                    'max_prices': [float(item['max_price']) for item in brand_price_data],
                    'car_counts': [item['car_count'] for item in brand_price_data]
                }
                
                if brand_price_data:
                    top_brands = brand_price_data[:5]
                    summary = f"价格最高的五个品牌是：{', '.join([item['car_model__brand__name'] for item in top_brands])}，"
                    summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_brands])}"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            # 其他价格分析类型...
            elif analysis_type == 'region_price':
                # 按地区分析价格
                cars = UsedCar.objects.filter(**query_filters)
                region_price_data = cars.values('location').annotate(
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
                
                if region_price_data:
                    top_regions = region_price_data[:5]
                    summary = f"价格最高的五个地区是：{', '.join([item['location'] for item in top_regions])}，"
                    summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_regions])}"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'year_price':
                # 按年份分析价格
                cars = UsedCar.objects.filter(**query_filters)
                year_price_data = cars.extra(
                    select={'year': 'EXTRACT(year FROM registration_date)'}
                ).values('year').annotate(
                    avg_price=Avg('price'),
                    min_price=Min('price'),
                    max_price=Max('price'),
                    car_count=Count('id')
                ).filter(car_count__gte=3).order_by('year')
                
                result_data = {
                    'years': [int(item['year']) for item in year_price_data],
                    'avg_prices': [float(item['avg_price']) for item in year_price_data],
                    'min_prices': [float(item['min_price']) for item in year_price_data],
                    'max_prices': [float(item['max_price']) for item in year_price_data],
                    'car_counts': [item['car_count'] for item in year_price_data]
                }
                
                if year_price_data:
                    summary = f"分析了{len(year_price_data)}个年份的价格分布，年份范围从{min(result_data['years'])}年到{max(result_data['years'])}年。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'mileage_price':
                # 按里程分析价格
                cars = UsedCar.objects.filter(**query_filters)
                # 将里程分组
                mileage_ranges = [
                    (0, 1, '0-1万公里'),
                    (1, 3, '1-3万公里'),
                    (3, 5, '3-5万公里'),
                    (5, 8, '5-8万公里'),
                    (8, 12, '8-12万公里'),
                    (12, 20, '12-20万公里'),
                    (20, 999, '20万公里以上')
                ]
                
                mileage_data = []
                for min_m, max_m, label in mileage_ranges:
                    range_cars = cars.filter(mileage__gte=min_m, mileage__lt=max_m)
                    if range_cars.exists():
                        stats = range_cars.aggregate(
                            avg_price=Avg('price'),
                            min_price=Min('price'),
                            max_price=Max('price'),
                            car_count=Count('id')
                        )
                        if stats['car_count'] >= 3:
                            mileage_data.append({
                                'range': label,
                                'avg_price': float(stats['avg_price']),
                                'min_price': float(stats['min_price']),
                                'max_price': float(stats['max_price']),
                                'car_count': stats['car_count']
                            })
                
                result_data = {
                    'ranges': [item['range'] for item in mileage_data],
                    'avg_prices': [item['avg_price'] for item in mileage_data],
                    'min_prices': [item['min_price'] for item in mileage_data],
                    'max_prices': [item['max_price'] for item in mileage_data],
                    'car_counts': [item['car_count'] for item in mileage_data]
                }
                
                if mileage_data:
                    summary = f"分析了{len(mileage_data)}个里程区间的价格分布。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
        
        elif analysis_category == 'brand':
            if analysis_type == 'brand_popularity':
                # 按品牌统计车辆数量
                cars = UsedCar.objects.filter(**query_filters)
                brand_count_data = cars.values('car_model__brand__name').annotate(
                    car_count=Count('id')
                ).order_by('-car_count')
                
                result_data = {
                    'brands': [item['car_model__brand__name'] for item in brand_count_data],
                    'counts': [item['car_count'] for item in brand_count_data]
                }
                
                if brand_count_data:
                    top_brands = brand_count_data[:5]
                    summary = f"车辆数量最多的五个品牌是：{', '.join([item['car_model__brand__name'] for item in top_brands])}，"
                    summary += f"车辆数量分别为：{', '.join([str(item['car_count']) + '辆' for item in top_brands])}"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'brand_price_range':
                # 品牌价格水平分析
                cars = UsedCar.objects.filter(**query_filters)
                brand_price_data = cars.values('car_model__brand__name').annotate(
                    avg_price=Avg('price'),
                    car_count=Count('id')
                ).filter(car_count__gte=3).order_by('-avg_price')
                
                result_data = {
                    'brands': [item['car_model__brand__name'] for item in brand_price_data],
                    'avg_prices': [float(item['avg_price']) for item in brand_price_data],
                    'counts': [item['car_count'] for item in brand_price_data]
                }
                
                if brand_price_data:
                    summary = f"分析了{len(brand_price_data)}个品牌的价格水平。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'brand_region_distribution':
                # 品牌地区分布分析
                cars = UsedCar.objects.filter(**query_filters)
                brand_region_data = cars.values('car_model__brand__name', 'location').annotate(
                    car_count=Count('id')
                ).order_by('car_model__brand__name', '-car_count')
                
                # 组织数据
                brand_distribution = {}
                for item in brand_region_data:
                    brand = item['car_model__brand__name']
                    if brand not in brand_distribution:
                        brand_distribution[brand] = []
                    brand_distribution[brand].append({
                        'region': item['location'],
                        'count': item['car_count']
                    })
                
                result_data = brand_distribution
                
                if brand_distribution:
                    summary = f"分析了{len(brand_distribution)}个品牌在各地区的分布情况。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
        
        elif analysis_category == 'region':
            if analysis_type == 'region_car_count':
                # 按地区统计车辆数量
                cars = UsedCar.objects.filter(**query_filters)
                region_count_data = cars.values('location').annotate(
                    car_count=Count('id')
                ).order_by('-car_count')
                
                result_data = {
                    'regions': [item['location'] for item in region_count_data],
                    'counts': [item['car_count'] for item in region_count_data]
                }
                
                if region_count_data:
                    top_regions = region_count_data[:5]
                    summary = f"车辆数量最多的五个地区是：{', '.join([item['location'] for item in top_regions])}，"
                    summary += f"车辆数量分别为：{', '.join([str(item['car_count']) + '辆' for item in top_regions])}"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'region_price_level':
                # 地区价格水平分析
                cars = UsedCar.objects.filter(**query_filters)
                region_price_data = cars.values('location').annotate(
                    avg_price=Avg('price'),
                    car_count=Count('id')
                ).filter(car_count__gte=3).order_by('-avg_price')
                
                result_data = {
                    'regions': [item['location'] for item in region_price_data],
                    'avg_prices': [float(item['avg_price']) for item in region_price_data],
                    'counts': [item['car_count'] for item in region_price_data]
                }
                
                if region_price_data:
                    summary = f"分析了{len(region_price_data)}个地区的价格水平。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
            elif analysis_type == 'region_brand_preference':
                # 地区品牌偏好分析
                cars = UsedCar.objects.filter(**query_filters)
                region_brand_data = cars.values('location', 'car_model__brand__name').annotate(
                    car_count=Count('id')
                ).order_by('location', '-car_count')
                
                # 组织数据
                region_preference = {}
                for item in region_brand_data:
                    region = item['location']
                    if region not in region_preference:
                        region_preference[region] = []
                    region_preference[region].append({
                        'brand': item['car_model__brand__name'],
                        'count': item['car_count']
                    })
                
                result_data = region_preference
                
                if region_preference:
                    summary = f"分析了{len(region_preference)}个地区的品牌偏好情况。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
        
        elif analysis_category == 'vehicle':
            if analysis_type == 'fuel_type_analysis':
                result_data, summary = VehicleAttributeAnalysisService.analyze_fuel_type()
            elif analysis_type == 'transmission_analysis':
                result_data, summary = VehicleAttributeAnalysisService.analyze_transmission()
            elif analysis_type == 'color_preference':
                result_data, summary = VehicleAttributeAnalysisService.analyze_color_preference()
            elif analysis_type == 'engine_type_analysis':
                result_data, summary = VehicleAttributeAnalysisService.analyze_engine_type()
            elif analysis_type == 'mileage_distribution':
                # 里程分布分析
                cars = UsedCar.objects.filter(**query_filters)
                mileage_ranges = [
                    (0, 1, '0-1万公里'),
                    (1, 3, '1-3万公里'),
                    (3, 5, '3-5万公里'),
                    (5, 8, '5-8万公里'),
                    (8, 12, '8-12万公里'),
                    (12, 20, '12-20万公里'),
                    (20, 999, '20万公里以上')
                ]
                
                mileage_data = []
                for min_m, max_m, label in mileage_ranges:
                    count = cars.filter(mileage__gte=min_m, mileage__lt=max_m).count()
                    if count > 0:
                        mileage_data.append({
                            'range': label,
                            'count': count
                        })
                
                result_data = {
                    'ranges': [item['range'] for item in mileage_data],
                    'counts': [item['count'] for item in mileage_data]
                }
                
                if mileage_data:
                    summary = f"分析了{len(mileage_data)}个里程区间的车辆分布。"
                else:
                    summary = "根据当前筛选条件，未找到符合条件的数据。"
        
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

@login_required
@csrf_exempt
def export_analysis(request):
    """导出分析结果到Excel"""
    if request.method != 'POST':
        return JsonResponse({'error': '只支持POST请求'}, status=405)
    
    try:
        data = json.loads(request.body)
        analysis_category = data.get('analysis_category')
        analysis_type = data.get('analysis_type')
        result_data = data.get('result_data', {})
        filter_data = data.get('filter_data', {})
        
        # 创建Excel文件
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 根据分析类型创建不同的工作表
            if analysis_category == 'price':
                if analysis_type == 'brand_price':
                    df = pd.DataFrame({
                        '品牌': result_data.get('brands', []),
                        '平均价格(万元)': result_data.get('avg_prices', []),
                        '最低价格(万元)': result_data.get('min_prices', []),
                        '最高价格(万元)': result_data.get('max_prices', []),
                        '车辆数量': result_data.get('car_counts', [])
                    })
                    df.to_excel(writer, sheet_name='品牌价格分析', index=False)
                    
                elif analysis_type == 'region_price':
                    df = pd.DataFrame({
                        '地区': result_data.get('regions', []),
                        '平均价格(万元)': result_data.get('avg_prices', []),
                        '最低价格(万元)': result_data.get('min_prices', []),
                        '最高价格(万元)': result_data.get('max_prices', []),
                        '车辆数量': result_data.get('car_counts', [])
                    })
                    df.to_excel(writer, sheet_name='地区价格分析', index=False)
                    
                elif analysis_type == 'year_price':
                    df = pd.DataFrame({
                        '年份': result_data.get('years', []),
                        '平均价格(万元)': result_data.get('avg_prices', []),
                        '最低价格(万元)': result_data.get('min_prices', []),
                        '最高价格(万元)': result_data.get('max_prices', []),
                        '车辆数量': result_data.get('car_counts', [])
                    })
                    df.to_excel(writer, sheet_name='年份价格分析', index=False)
                    
                elif analysis_type == 'mileage_price':
                    df = pd.DataFrame({
                        '里程范围': result_data.get('mileage_ranges', []),
                        '平均价格(万元)': result_data.get('avg_prices', []),
                        '最低价格(万元)': result_data.get('min_prices', []),
                        '最高价格(万元)': result_data.get('max_prices', []),
                        '车辆数量': result_data.get('car_counts', [])
                    })
                    df.to_excel(writer, sheet_name='里程价格分析', index=False)
                    
            elif analysis_category == 'brand':
                # 品牌分析导出
                if 'brands' in result_data and 'values' in result_data:
                    df = pd.DataFrame({
                        '品牌': result_data.get('brands', []),
                        '数值': result_data.get('values', [])
                    })
                    df.to_excel(writer, sheet_name='品牌分析', index=False)
                    
            elif analysis_category == 'region':
                # 地区分析导出
                if 'regions' in result_data and 'values' in result_data:
                    df = pd.DataFrame({
                        '地区': result_data.get('regions', []),
                        '数值': result_data.get('values', [])
                    })
                    df.to_excel(writer, sheet_name='地区分析', index=False)
                    
            elif analysis_category == 'vehicle':
                # 车辆属性分析导出
                if 'labels' in result_data and 'values' in result_data:
                    df = pd.DataFrame({
                        '属性': result_data.get('labels', []),
                        '数值': result_data.get('values', [])
                    })
                    df.to_excel(writer, sheet_name='车辆属性分析', index=False)
            
            # 添加过滤条件工作表
            if filter_data:
                filter_df = pd.DataFrame([
                    {'过滤条件': key, '值': str(value)} 
                    for key, value in filter_data.items() if value
                ])
                if not filter_df.empty:
                    filter_df.to_excel(writer, sheet_name='过滤条件', index=False)
        
        output.seek(0)
        
        # 设置响应
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f'数据分析结果_{analysis_category}_{analysis_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'导出失败: {str(e)}'}, status=500)