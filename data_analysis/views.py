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
    

    
    # 获取最新的分析结果
    latest_price_analysis = price_analysis
    latest_region_analysis = region_analysis
    
    context = {
        'total_cars': total_cars,
        'total_brands': total_brands,
        'avg_price': avg_price,
        'latest_price_analysis': latest_price_analysis,
        'latest_region_analysis': latest_region_analysis,
    }
    return render(request, 'data_analysis/index.html', context)

@login_required
def price_analysis(request):
    """价格分析页面"""
    analysis_type = request.GET.get('type', 'brand_price')
    
    # 如果是AJAX请求，返回JSON数据
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return price_analysis_data(request)
    
    context = {
        'analysis_type': analysis_type,
        'analysis_types': {
            'brand_price': '品牌价格分析',
            'region_price': '地区价格分析', 
            'year_price': '年份价格分析',
            'mileage_price': '里程价格分析'
        },
    }
    return render(request, 'data_analysis/price_analysis.html', context)

@login_required
def price_analysis_data(request):
    """价格分析数据API - 参考admin后台实现"""
    try:
        analysis_type = request.GET.get('type', 'brand_price')
        export_to_excel = request.GET.get('export', 'false') == 'true'
        
        # 获取筛选条件 - 支持多选
        brands = request.GET.getlist('brands')  # 多选品牌
        regions = request.GET.getlist('regions')  # 多选地区
        fuel_types = request.GET.getlist('fuel_types')  # 多选燃料类型
        
        # 日期范围
        date_from = request.GET.get('registration_date_from', '')
        date_to = request.GET.get('registration_date_to', '')
        
        # 价格和里程范围
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        min_mileage = request.GET.get('min_mileage', '')
        max_mileage = request.GET.get('max_mileage', '')
        
        print(f"[DEBUG] 价格分析API调用 - 分析类型: {analysis_type}")
        print(f"[DEBUG] 筛选条件 - 品牌: {brands}, 地区: {regions}, 燃料类型: {fuel_types}")
        print(f"[DEBUG] 日期范围: {date_from} 到 {date_to}")
        print(f"[DEBUG] 价格范围: {min_price}-{max_price}, 里程范围: {min_mileage}-{max_mileage}")
        
        # 构建基础查询集
        queryset = UsedCar.objects.all()
        
        # 应用筛选条件
        if brands:
            queryset = queryset.filter(car_model__brand__name__in=brands)
        if regions:
            queryset = queryset.filter(location__in=regions)
        if fuel_types:
            queryset = queryset.filter(fuel_type__in=fuel_types)
         
        # 日期范围筛选
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__lte=date_to_obj)
            except ValueError:
                pass
         
        # 价格范围筛选
        if min_price:
            try:
                min_price_float = float(min_price)
                queryset = queryset.filter(price__gte=min_price_float)
            except ValueError:
                pass
        if max_price:
            try:
                max_price_float = float(max_price)
                queryset = queryset.filter(price__lte=max_price_float)
            except ValueError:
                pass
        
        # 里程范围筛选
        if min_mileage:
            try:
                min_mileage_float = float(min_mileage)
                queryset = queryset.filter(mileage__gte=min_mileage_float)
            except ValueError:
                pass
        if max_mileage:
            try:
                max_mileage_float = float(max_mileage)
                queryset = queryset.filter(mileage__lte=max_mileage_float)
            except ValueError:
                pass
        
        print(f"[DEBUG] 筛选后的查询集总数: {queryset.count()}")
        
        # 根据分析类型进行数据分析 - 参考admin后台实现
        if analysis_type == 'brand_price':
             # 过滤掉价格为空或无效的数据，限制返回数量防止性能问题
             data = queryset.exclude(price__isnull=True).exclude(price__lte=0).values('car_model__brand__name').annotate(
                 avg_price=Avg('price'),
                 min_price=Min('price'),
                 max_price=Max('price'),
                 car_count=Count('id')
             ).filter(car_count__gte=3).order_by('-avg_price')
             
             print(f"[DEBUG] 品牌价格分析数据条数: {len(data)}")
             
             result = {
                 'labels': [item['car_model__brand__name'] for item in data],
                 'values': [float(item['avg_price']) for item in data],
                 'min_values': [float(item['min_price']) for item in data],
                 'max_values': [float(item['max_price']) for item in data],
                 'counts': [item['car_count'] for item in data],
                 'detailed_data': [{
                     'min_price': float(item['min_price']),
                     'max_price': float(item['max_price']),
                     'car_count': item['car_count']
                 } for item in data],
                 'title': '品牌平均价格(万元)',
                 'type': 'bar'
             }
        
        elif analysis_type == 'region_price':
            # 过滤掉价格为空、地区为空或无效的数据，限制返回数量防止性能问题
            data = queryset.exclude(price__isnull=True).exclude(price__lte=0).exclude(location__isnull=True).exclude(location='').values('location').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('-avg_price')
            
            print(f"[DEBUG] 地区价格分析数据条数: {len(data)}")
            
            result = {
                'labels': [item['location'] for item in data],
                'regions': [item['location'] for item in data],  # 添加 regions 属性以保持兼容性
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'detailed_data': [{
                    'min_price': float(item['min_price']),
                    'max_price': float(item['max_price']),
                    'car_count': item['car_count']
                } for item in data],
                'title': '地区平均价格(万元)',
                'type': 'bar'
            }
        
        elif analysis_type == 'year_price':
            # 由于first_registration是字符串字段，我们需要提取年份进行分析
            # 过滤掉价格为空、首次上牌为空的数据
            valid_cars = queryset.exclude(price__isnull=True).exclude(price__lte=0).exclude(registration_date__isnull=True)
            
            # 手动提取年份并分组
            year_data = {}
            for car in valid_cars:
                # 从registration_date字段中提取年份
                if car.registration_date:
                    year = str(car.registration_date.year)
                    if year not in year_data:
                        year_data[year] = {'prices': [], 'count': 0}
                    year_data[year]['prices'].append(float(car.price))
                    year_data[year]['count'] += 1
            
            # 计算每年的统计数据
            data = []
            for year, info in sorted(year_data.items()):
                if info['count'] >= 3:  # 至少3辆车才显示
                    prices = info['prices']
                    data.append({
                        'year': year,
                        'avg_price': sum(prices) / len(prices),
                        'min_price': min(prices),
                        'max_price': max(prices),
                        'car_count': info['count']
                    })
            
            print(f"[DEBUG] 年份价格分析数据条数: {len(data)}")
        
            result = {
                'labels': [item['year'] for item in data],
                'values': [item['avg_price'] for item in data],
                'min_values': [item['min_price'] for item in data],
                'max_values': [item['max_price'] for item in data],
                'counts': [item['car_count'] for item in data],
                'detailed_data': [{
                    'min_price': item['min_price'],
                    'max_price': item['max_price'],
                    'car_count': item['car_count']
                } for item in data],
                'title': '年份平均价格(万元)',
                'type': 'line'
            }
        
        elif analysis_type == 'mileage_price':
            # 创建里程范围，过滤掉价格和里程为空或无效的数据
            ranges = [(0, 2), (2, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, float('inf'))]
            data = []
            
            for i, (start, end) in enumerate(ranges):
                if end == float('inf'):
                    range_data = queryset.exclude(price__isnull=True).exclude(price__lte=0).exclude(mileage__isnull=True).filter(mileage__gte=start).aggregate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price'),
                        car_count=Count('id')
                    )
                    label = f'{start}万公里以上'
                else:
                    range_data = queryset.exclude(price__isnull=True).exclude(price__lte=0).exclude(mileage__isnull=True).filter(mileage__gte=start, mileage__lt=end).aggregate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price'),
                        car_count=Count('id')
                    )
                    label = f'{start}-{end}万公里'
                
                if range_data['car_count'] and range_data['car_count'] > 0:
                    data.append({
                        'range': label,
                        'avg_price': range_data['avg_price'],
                        'min_price': range_data['min_price'],
                        'max_price': range_data['max_price'],
                        'car_count': range_data['car_count']
                    })
            
            print(f"[DEBUG] 里程价格分析数据条数: {len(data)}")
            
            result = {
                'labels': [item['range'] for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'detailed_data': [{
                    'min_price': float(item['min_price']),
                    'max_price': float(item['max_price']),
                    'car_count': item['car_count']
                } for item in data],
                'title': '里程与平均价格关系(万元)',
                'type': 'line'
            }
        
        else:
            result = {
                'labels': [],
                'values': [],
                'title': '未知分析类型',
                'type': 'bar',
                'error': f'不支持的分析类型: {analysis_type}'
            }
        
        # 添加统计摘要，过滤掉价格为空或无效的数据
        valid_price_queryset = queryset.exclude(price__isnull=True).exclude(price__lte=0)
        result['summary'] = {
            'total_count': queryset.count(),
            'brand_count': valid_price_queryset.count(),  # 修改字段名以匹配前端
            'avg_price': float(valid_price_queryset.aggregate(avg_price=Avg('price'))['avg_price'] or 0),
            'min_price': float(valid_price_queryset.aggregate(min_price=Min('price'))['min_price'] or 0),
            'max_price': float(valid_price_queryset.aggregate(max_price=Max('price'))['max_price'] or 0),
        }
        
        print(f"[DEBUG] 最终结果摘要: {result['summary']}")
        
        # 处理Excel导出
        if export_to_excel:
            import pandas as pd
            from django.http import HttpResponse
            import io
            
            if 'labels' in result and result['labels']:
                if analysis_type == 'brand_price':
                    df_data = {
                        '品牌': result['labels'],
                        '平均价格(万元)': result['values'],
                        '最低价格(万元)': result['min_values'],
                        '最高价格(万元)': result['max_values'],
                        '车辆数量': result['counts'],
                    }
                elif analysis_type == 'region_price':
                    df_data = {
                        '地区': result['labels'],
                        '平均价格(万元)': result['values'],
                        '最低价格(万元)': result['min_values'],
                        '最高价格(万元)': result['max_values'],
                        '车辆数量': result['counts'],
                    }
                elif analysis_type == 'year_price':
                    df_data = {
                        '年份': result['labels'],
                        '平均价格(万元)': result['values'],
                        '最低价格(万元)': result['min_values'],
                        '最高价格(万元)': result['max_values'],
                        '车辆数量': result['counts'],
                    }
                elif analysis_type == 'mileage_price':
                    df_data = {
                        '里程范围': result['labels'],
                        '平均价格(万元)': result['values'],
                        '最低价格(万元)': result['min_values'],
                        '最高价格(万元)': result['max_values'],
                        '车辆数量': result['counts'],
                    }
                
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='PriceAnalysis')
                
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}',
            'labels': [],
            'values': [],
            'title': '分析失败',
            'type': 'bar',
            'summary': {'total_count': 0, 'brand_count': 0}
        }, status=500)





@login_required
def region_analysis_data(request):
    """地区分析数据API"""
    try:
        analysis_type = request.GET.get('analysis_type', 'region_car_count')
        export_to_excel = request.GET.get('export', 'false') == 'true'
        
        # 获取筛选条件
        brands = request.GET.getlist('brands')
        regions = request.GET.getlist('regions')
        fuel_types = request.GET.getlist('fuel_types')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        min_mileage = request.GET.get('min_mileage', '')
        max_mileage = request.GET.get('max_mileage', '')
        
        # 构建基础查询集
        queryset = UsedCar.objects.all()
        
        # 应用筛选条件
        if brands:
            queryset = queryset.filter(car_model__brand__name__in=brands)
        if regions:
            queryset = queryset.filter(location__in=regions)
        if fuel_types:
            queryset = queryset.filter(fuel_type__in=fuel_types)
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__lte=date_to_obj)
            except ValueError:
                pass
        if min_price:
            try:
                min_price_float = float(min_price)
                queryset = queryset.filter(price__gte=min_price_float)
            except ValueError:
                pass
        if max_price:
            try:
                max_price_float = float(max_price)
                queryset = queryset.filter(price__lte=max_price_float)
            except ValueError:
                pass
        if min_mileage:
            try:
                min_mileage_float = float(min_mileage)
                queryset = queryset.filter(mileage__gte=min_mileage_float)
            except ValueError:
                pass
        if max_mileage:
            try:
                max_mileage_float = float(max_mileage)
                queryset = queryset.filter(mileage__lte=max_mileage_float)
            except ValueError:
                pass
        
        # 根据分析类型进行数据分析
        if analysis_type == 'region_car_count':
            data = queryset.exclude(location__isnull=True).exclude(location='').values('location').annotate(
                car_count=Count('id')
            ).filter(car_count__gt=0).order_by('-car_count')[:30]
            
            result = {
                'labels': [item['location'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '地区车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'region_price_level':
            data = queryset.exclude(location__isnull=True).exclude(location='').exclude(price__isnull=True).values('location').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('-avg_price')[:30]
            
            result = {
                'labels': [item['location'] for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '地区价格水平(万元)',
                'type': 'bar'
            }
        
        elif analysis_type == 'region_brand_preference':
            # 获取主要地区
            major_regions = queryset.exclude(location__isnull=True).exclude(location='').values('location').annotate(
                car_count=Count('id')
            ).filter(car_count__gte=5).order_by('-car_count')[:10]
            
            region_brand_data = []
            for region_data in major_regions:
                region_name = region_data['location']
                # 获取该地区的品牌偏好
                brand_counts = queryset.filter(
                    location=region_name
                ).exclude(car_model__brand__name__isnull=True).exclude(car_model__brand__name='').values('car_model__brand__name').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]  # 取前5个品牌
                
                if brand_counts:
                    region_brand_data.append({
                        'region': region_name,
                        'brands': [brand['car_model__brand__name'] for brand in brand_counts],
                        'counts': [brand['count'] for brand in brand_counts]
                    })
            
            # 构建结果数据
            if region_brand_data:
                # 取第一个地区的数据作为示例
                first_region = region_brand_data[0]
                result = {
                    'labels': first_region['brands'],
                    'values': first_region['counts'],
                    'title': f'{first_region["region"]}地区品牌偏好',
                    'type': 'pie',
                    'region_data': region_brand_data
                }
            else:
                result = {
                    'labels': [],
                    'values': [],
                    'title': '地区品牌偏好',
                    'type': 'pie',
                    'region_data': []
                }
        
        else:
            result = {
                'labels': [],
                'values': [],
                'title': '未知分析类型',
                'type': 'bar',
                'error': f'不支持的分析类型: {analysis_type}'
            }
    
        # 添加统计摘要
        result['summary'] = {
            'total_count': queryset.count(),
            'region_count': queryset.exclude(location__isnull=True).exclude(location='').values('location').distinct().count(),
        }
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}',
            'labels': [],
            'values': [],
            'title': '分析失败',
            'type': 'bar',
            'summary': {'total_count': 0, 'brand_count': 0}
        }, status=500)



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
    # 如果是AJAX请求，返回JSON数据
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return interactive_analysis_data(request)
    
    # 获取可用的数据源（从实际使用的车辆中获取品牌）
    brands = UsedCar.objects.exclude(car_model__brand__isnull=True).values_list('car_model__brand__name', flat=True).distinct().order_by('car_model__brand__name')
    brand_objects = [{'name': brand} for brand in brands if brand]
    regions = UsedCar.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct()
    
    # 获取年份范围 (SQLite兼容)
    years = UsedCar.objects.exclude(registration_date__isnull=True).extra(
        select={'year': "strftime('%Y', registration_date)"}
    ).values_list('year', flat=True).distinct().order_by('year')
    
    context = {
        'brands': brand_objects,
        'regions': list(regions),
        'years': [int(year) for year in years if year],
        'analysis_types': {
            'price_by_brand': '品牌价格分析',
            'price_by_region': '地区价格分析',
            'price_by_year': '年份价格分析',
            'price_by_mileage': '里程价格分析',
            'count_by_brand': '品牌数量分析',
            'count_by_region': '地区数量分析',
            'count_by_fuel': '燃料类型分析',
            'count_by_transmission': '变速箱类型分析',
        }
    }
    return render(request, 'data_analysis/interactive_analysis.html', context)

@login_required
def interactive_analysis_data(request):
    """交互式分析数据API"""
    try:
        analysis_type = request.GET.get('analysis_type', 'price_by_brand')
        export_to_excel = request.GET.get('export', 'false') == 'true'
        
        # 获取筛选条件
        brands = request.GET.getlist('brands')
        regions = request.GET.getlist('regions')
        brand_filter = request.GET.get('brand', '')
        region_filter = request.GET.get('region', '')
        year_filter = request.GET.get('year', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        min_mileage = request.GET.get('min_mileage', '')
        max_mileage = request.GET.get('max_mileage', '')
        fuel_type = request.GET.get('fuel_type', '')
        transmission = request.GET.get('transmission', '')
        
        # 构建基础查询集
        queryset = UsedCar.objects.all()
    
        # 应用筛选条件
        if brands:
            queryset = queryset.filter(car_model__brand__name__in=brands)
        elif brand_filter:
            queryset = queryset.filter(car_model__brand__name__icontains=brand_filter)
        if regions:
            queryset = queryset.filter(location__in=regions)
        elif region_filter:
            queryset = queryset.filter(location__icontains=region_filter)
        if year_filter:
            try:
                year_int = int(year_filter)
                queryset = queryset.filter(registration_date__year=year_int)
            except ValueError:
                pass
        if min_price:
            try:
                min_price_float = float(min_price)
                queryset = queryset.filter(price__gte=min_price_float)
            except ValueError:
                pass
        if max_price:
            try:
                max_price_float = float(max_price)
                queryset = queryset.filter(price__lte=max_price_float)
            except ValueError:
                pass
        if min_mileage:
            try:
                min_mileage_float = float(min_mileage)
                queryset = queryset.filter(mileage__gte=min_mileage_float)
            except ValueError:
                pass
        if max_mileage:
            try:
                max_mileage_float = float(max_mileage)
                queryset = queryset.filter(mileage__lte=max_mileage_float)
            except ValueError:
                pass
        if fuel_type:
            queryset = queryset.filter(fuel_type__icontains=fuel_type)
        if transmission:
            queryset = queryset.filter(gearbox__icontains=transmission)
    
        # 根据分析类型进行数据分析（参考admin后台的实现）
        if analysis_type == 'price_by_brand':
            data = queryset.exclude(car_model__brand__name__isnull=True).exclude(car_model__brand__name='').exclude(price__isnull=True).values('car_model__brand__name').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=1).order_by('-avg_price')[:30]
            
            result = {
                'labels': [item['car_model__brand__name'] for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '品牌平均价格(万元)',
                'type': 'bar'
            }
        
        elif analysis_type == 'price_by_region':
            data = queryset.exclude(location__isnull=True).exclude(location='').exclude(price__isnull=True).values('location').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=1).order_by('-avg_price')[:30]
            
            result = {
                'labels': [item['location'] for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '地区平均价格(万元)',
                'type': 'bar'
            }
        
        elif analysis_type == 'price_by_year':
            data = queryset.exclude(registration_date__isnull=True).exclude(price__isnull=True).extra(
                select={'year': "strftime('%Y', registration_date)"}
            ).values('year').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=1).order_by('year')
            
            result = {
                'labels': [str(int(item['year'])) for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '年份平均价格(万元)',
                'type': 'line'
            }
        
        elif analysis_type == 'price_by_mileage':
            # 定义里程区间
            mileage_ranges = [
                (0, 1, '0-1万公里'),
                (1, 3, '1-3万公里'),
                (3, 5, '3-5万公里'),
                (5, 8, '5-8万公里'),
                (8, 10, '8-10万公里'),
                (10, 15, '10-15万公里'),
                (15, float('inf'), '15万公里以上')
            ]
            
            data = []
            for start, end, label in mileage_ranges:
                if end == float('inf'):
                    range_queryset = queryset.filter(mileage__gte=start).exclude(price__isnull=True)
                else:
                    range_queryset = queryset.filter(mileage__gte=start, mileage__lt=end).exclude(price__isnull=True)
                
                if range_queryset.exists():
                    range_data = range_queryset.aggregate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price'),
                        car_count=Count('id')
                    )
                    data.append({
                        'range': label,
                        'avg_price': range_data['avg_price'],
                        'min_price': range_data['min_price'],
                        'max_price': range_data['max_price'],
                        'car_count': range_data['car_count']
                    })
            
            result = {
                'labels': [item['range'] for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '里程与平均价格关系(万元)',
                'type': 'line'
            }
        
        elif analysis_type == 'count_by_brand':
            data = queryset.exclude(car_model__brand__name__isnull=True).exclude(car_model__brand__name='').values('car_model__brand__name').annotate(
                car_count=Count('id')
            ).filter(car_count__gt=0).order_by('-car_count')[:30]
            
            result = {
                'labels': [item['car_model__brand__name'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '品牌车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'count_by_region':
            data = queryset.exclude(location__isnull=True).exclude(location='').values('location').annotate(
                car_count=Count('id')
            ).filter(car_count__gt=0).order_by('-car_count')[:30]
            
            result = {
                'labels': [item['location'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '地区车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'count_by_fuel':
            data = queryset.exclude(fuel_type__isnull=True).exclude(fuel_type='').values('fuel_type').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['fuel_type'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '燃料类型分布',
                'type': 'pie'
            }
        
        elif analysis_type == 'count_by_transmission':
            data = queryset.exclude(gearbox__isnull=True).exclude(gearbox='').values('gearbox').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['gearbox'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '变速箱类型分布',
                'type': 'pie'
            }
        
        else:
            result = {
                'labels': [],
                'values': [],
                'title': '未知分析类型',
                'type': 'bar',
                'error': f'不支持的分析类型: {analysis_type}'
            }
        
        # 添加统计摘要
        valid_price_queryset = queryset.exclude(price__isnull=True).exclude(price__lte=0)
        result['summary'] = {
            'total_count': queryset.count(),
            'brand_count': valid_price_queryset.count(),  # 修改字段名以匹配前端
            'avg_price': float(valid_price_queryset.aggregate(avg_price=Avg('price'))['avg_price'] or 0),
            'min_price': float(valid_price_queryset.aggregate(min_price=Min('price'))['min_price'] or 0),
            'max_price': float(valid_price_queryset.aggregate(max_price=Max('price'))['max_price'] or 0),
        }
        
        # 处理Excel导出
        if export_to_excel:
            import pandas as pd
            from django.http import HttpResponse
            import io
            
            if 'labels' in result and result['labels']:
                if analysis_type.startswith('price_'):
                    df_data = {
                        '类别': result['labels'],
                        '平均价格(万元)': result['values'],
                    }
                    if 'min_values' in result:
                        df_data['最低价格(万元)'] = result['min_values']
                        df_data['最高价格(万元)'] = result['max_values']
                    if 'counts' in result:
                        df_data['车辆数量'] = result['counts']
                elif analysis_type.startswith('count_'):
                    total_count_for_percentage = sum(result['values'])
                    percentages = [(val / total_count_for_percentage * 100) if total_count_for_percentage > 0 else 0 for val in result['values']]
                    df_data = {
                        '类别': result['labels'],
                        '数量': result['values'],
                        '占比(%)': [f"{p:.2f}%" for p in percentages]
                    }
                
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='InteractiveAnalysis')
                
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}',
            'labels': [],
            'values': [],
            'title': '分析失败',
            'type': 'bar',
            'summary': {'total_count': 0, 'brand_count': 0}
        }, status=500)

@login_required
def old_interactive_analysis(request):
    """旧的交互式数据分析页面（保留作为备份）"""
    # 获取可用的数据源（从实际使用的车辆中获取品牌）
    brands = UsedCar.objects.exclude(car_model__brand__isnull=True).values_list('car_model__brand__name', flat=True).distinct().order_by('car_model__brand__name')
    brand_objects = [{'name': brand} for brand in brands if brand]
    regions = UsedCar.objects.values_list('location', flat=True).distinct()
    
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
                    select={'year': "strftime('%Y', registration_date)"}
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
        'brands': brand_objects,
        'regions': regions,
        'price_analysis_types': price_analysis_types,
        'brand_analysis_types': brand_analysis_types,
        'region_analysis_types': region_analysis_types,
        'vehicle_analysis_types': vehicle_analysis_types,
    }
    return render(request, 'data_analysis/interactive_analysis.html', context)

@login_required
def get_filter_options(request):
    """获取筛选选项数据API"""
    try:
        # 调试：检查数据库中的总车辆数
        total_cars = UsedCar.objects.count()
        print(f"[DEBUG] 数据库中总车辆数: {total_cars}")
        
        # 调试：检查有品牌信息的车辆数
        cars_with_brand = UsedCar.objects.exclude(car_model__brand__isnull=True).count()
        print(f"[DEBUG] 有品牌信息的车辆数: {cars_with_brand}")
        
        # 获取所有品牌（通过car_model关联获取）
        brands = UsedCar.objects.exclude(car_model__brand__isnull=True).values_list('car_model__brand__name', flat=True).distinct().order_by('car_model__brand__name')
        brand_list = [{'name': brand} for brand in brands if brand]
        print(f"[DEBUG] 获取到的品牌数量: {len(brand_list)}")
        print(f"[DEBUG] 前5个品牌: {brand_list[:5]}")
        
        # 获取所有地区（去重）
        regions = UsedCar.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
        region_list = [{'name': region} for region in regions]
        print(f"[DEBUG] 获取到的地区数量: {len(region_list)}")
        print(f"[DEBUG] 前5个地区: {region_list[:5]}")
        
        # 获取年份范围 (SQLite兼容)
        year_range = UsedCar.objects.exclude(registration_date__isnull=True).extra(
            select={'year': "strftime('%Y', registration_date)"}
        ).values_list('year', flat=True).distinct().order_by('year')
        year_list = [{'year': int(year)} for year in year_range if year]
        print(f"[DEBUG] 获取到的年份数量: {len(year_list)}")
        print(f"[DEBUG] 年份范围: {year_list[:5] if year_list else '无'}")
        
        # 获取燃料类型（如果有的话）
        fuel_types = UsedCar.objects.exclude(fuel_type__isnull=True).exclude(fuel_type='').values_list('fuel_type', flat=True).distinct().order_by('fuel_type')
        fuel_type_list = [{'name': fuel_type} for fuel_type in fuel_types]
        print(f"[DEBUG] 获取到的燃料类型数量: {len(fuel_type_list)}")
        print(f"[DEBUG] 燃料类型: {fuel_type_list}")
        
        # 获取价格范围
        price_stats = UsedCar.objects.exclude(price__isnull=True).exclude(price__lte=0).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        print(f"[DEBUG] 价格统计: {price_stats}")
        
        # 获取里程范围
        mileage_stats = UsedCar.objects.exclude(mileage__isnull=True).aggregate(
            min_mileage=Min('mileage'),
            max_mileage=Max('mileage')
        )
        print(f"[DEBUG] 里程统计: {mileage_stats}")
        
        result_data = {
            'brands': brand_list,
            'regions': region_list,
            'years': year_list,
            'fuel_types': fuel_type_list,
            'price_range': {
                'min': float(price_stats['min_price'] or 0),
                'max': float(price_stats['max_price'] or 0)
            },
            'mileage_range': {
                'min': float(mileage_stats['min_mileage'] or 0),
                'max': float(mileage_stats['max_mileage'] or 0)
            }
        }
        
        print(f"[DEBUG] 返回的完整数据: {result_data}")
        
        return JsonResponse({
            'success': True,
            'data': result_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'获取筛选选项失败: {str(e)}'
        }, status=500)

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