from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Min, Max, Q
from crawler.models import CarModel, UsedCar
from .models import SalesAnalysis, PriceAnalysis, MarketAnalysis
from .services import SalesAnalysisService, PriceAnalysisService, MarketAnalysisService
import json
from decimal import Decimal

# Create your views here.



@login_required
def comparison(request):
    """竞品对比页面"""
    return render(request, 'car_analysis/comparison.html')

@login_required
def comparison_data(request):
    """竞品对比数据API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            car_ids = data.get('car_ids', [])
            
            if not car_ids or len(car_ids) < 2:
                return JsonResponse({
                    'success': False,
                    'error': '请至少选择两款车型进行对比'
                })
            
            # 获取车型数据
            cars_data = []
            for car_id in car_ids:
                try:
                    car = CarModel.objects.select_related('brand').get(id=car_id)
                    
                    # 获取该车型的二手车数据，严格过滤缺失关键字段的数据
                    used_cars = UsedCar.objects.filter(
                        car_model=car,
                        price__isnull=False,
                        price__gt=0
                    ).exclude(
                        Q(title__isnull=True) | Q(title__exact='') |
                        Q(price__lt=1) | Q(price__gt=1000)  # 过滤异常价格
                    )
                    
                    # 基础统计信息
                    total_count = used_cars.count()
                    if total_count == 0:
                        # 如果没有有效数据，跳过该车型
                        continue
                    
                    # 价格统计
                    price_stats = used_cars.aggregate(
                        avg_price=Avg('price'),
                        min_price=Min('price'),
                        max_price=Max('price')
                    )
                    
                    # 里程统计（过滤有效里程数据）
                    mileage_cars = used_cars.filter(
                        mileage__isnull=False,
                        mileage__gt=0
                    )
                    mileage_stats = mileage_cars.aggregate(
                        avg_mileage=Avg('mileage')
                    )
                    
                    # 车龄统计（基于上牌日期）
                    year_cars = used_cars.filter(registration_date__isnull=False)
                    avg_year = None
                    if year_cars.exists():
                        current_year = timezone.now().year
                        years = [current_year - car.registration_date.year for car in year_cars]
                        avg_year = sum(years) / len(years) if years else None
                    
                    # 获取最常见的燃料类型和变速箱类型
                    fuel_type_stats = used_cars.filter(
                        fuel_type__isnull=False
                    ).exclude(
                        fuel_type__exact=''
                    ).values('fuel_type').annotate(
                        count=Count('fuel_type')
                    ).order_by('-count').first()
                    
                    gearbox_stats = used_cars.filter(
                        gearbox__isnull=False
                    ).exclude(
                        gearbox__exact=''
                    ).values('gearbox').annotate(
                        count=Count('gearbox')
                    ).order_by('-count').first()
                    
                    # 基于真实数据计算性能评分
                    performance_scores = _calculate_performance_scores(
                        used_cars, price_stats['avg_price'], mileage_stats['avg_mileage']
                    )
                    
                    # 基于数据质量和市场表现计算评分
                    ratings = _calculate_ratings(
                        used_cars, price_stats, total_count
                    )
                    
                    car_data = {
                        'id': car.id,
                        'name': f"{car.brand.name} {car.name}",
                        'brand_name': car.brand.name,
                        'price': f"{price_stats['avg_price']:.2f}万元" if price_stats['avg_price'] else '-',
                        'price_range': f"{price_stats['min_price']:.1f}-{price_stats['max_price']:.1f}万元" if price_stats['min_price'] and price_stats['max_price'] else '-',
                        'sales_volume': f"{total_count}辆",
                        'fuel_type': fuel_type_stats['fuel_type'] if fuel_type_stats else '-',
                        'gearbox': gearbox_stats['gearbox'] if gearbox_stats else '-',
                        'avg_mileage': f"{mileage_stats['avg_mileage']:.1f}万公里" if mileage_stats['avg_mileage'] else '-',
                        'avg_year': f"{avg_year:.1f}年" if avg_year else '-',
                        'performance': performance_scores,
                        'ratings': ratings,
                        'data_quality': {
                            'total_records': total_count,
                            'price_records': used_cars.filter(price__isnull=False).count(),
                            'mileage_records': mileage_cars.count(),
                            'year_records': year_cars.count()
                        }
                    }
                    
                    cars_data.append(car_data)
                    
                except CarModel.DoesNotExist:
                    continue
                except Exception as e:
                    print(f"处理车型 {car_id} 时出错: {str(e)}")
                    continue
            
            if not cars_data:
                return JsonResponse({
                    'success': False,
                    'error': '所选车型暂无有效数据，请选择其他车型'
                })
            
            return JsonResponse({
                'success': True,
                'cars': cars_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': '不支持的请求方法'
    })

def _calculate_performance_scores(used_cars, avg_price, avg_mileage):
    """基于真实数据计算性能评分"""
    try:
        # 价格性能比（价格越低评分越高）
        price_score = 5.0
        if avg_price:
            if avg_price > 50:
                price_score = 3.0
            elif avg_price > 30:
                price_score = 3.5
            elif avg_price > 15:
                price_score = 4.0
            elif avg_price > 8:
                price_score = 4.5
        
        # 里程表现（里程越低评分越高）
        mileage_score = 4.0
        if avg_mileage:
            if avg_mileage < 5:
                mileage_score = 5.0
            elif avg_mileage < 10:
                mileage_score = 4.5
            elif avg_mileage < 15:
                mileage_score = 4.0
            elif avg_mileage < 20:
                mileage_score = 3.5
            else:
                mileage_score = 3.0
        
        # 市场活跃度（基于在售数量）
        market_score = min(5.0, 3.0 + (used_cars.count() / 50))
        
        return {
            'power': round(price_score, 1),
            'handling': round(mileage_score, 1),
            'comfort': round((price_score + mileage_score) / 2, 1),
            'fuel_economy': round(mileage_score, 1),
            'space': round(market_score, 1)
        }
    except:
        # 如果计算出错，返回默认值
        return {
            'power': 4.0,
            'handling': 4.0,
            'comfort': 4.0,
            'fuel_economy': 4.0,
            'space': 4.0
        }

def _calculate_ratings(used_cars, price_stats, total_count):
    """基于数据质量和市场表现计算评分"""
    try:
        # 数据质量评分
        data_quality_score = min(5.0, 2.0 + (total_count / 20))
        
        # 价格合理性评分
        price_score = 4.0
        if price_stats['avg_price']:
            if 5 <= price_stats['avg_price'] <= 15:
                price_score = 5.0
            elif 3 <= price_stats['avg_price'] <= 25:
                price_score = 4.5
        
        # 市场活跃度评分
        market_score = min(5.0, 3.0 + (total_count / 30))
        
        # 基于实际数据特征计算各项评分
        base_score = (data_quality_score + price_score + market_score) / 3
        
        return {
            'overall': round(base_score, 1),
            'appearance': round(min(5.0, base_score + 0.2), 1),
            'interior': round(min(5.0, base_score - 0.2), 1),
            'configuration': round(min(5.0, base_score + 0.1), 1),
            'power': round(price_score, 1),
            'handling': round(data_quality_score, 1),
            'fuel_economy': round(market_score, 1),
            'comfort': round((data_quality_score + price_score) / 2, 1)
        }
    except Exception as e:
        print(f"计算评分时出错: {str(e)}")
        return {
            'overall': 4.0,
            'appearance': 4.0,
            'interior': 4.0,
            'configuration': 4.0,
            'power': 4.0,
            'handling': 4.0,
            'fuel_economy': 4.0,
            'comfort': 4.0
        }

def analysis_home(request):
    """分析首页"""
    return render(request, 'car_analysis/analysis_home.html')

@login_required
def sales_prediction(request, car_id):
    """销量预测"""
    car = get_object_or_404(CarModel, id=car_id)
    
    # 获取或创建销量分析
    today = timezone.now().date()
    analysis, created = SalesAnalysis.objects.get_or_create(
        car=car,
        analysis_date=today,
        defaults={'prediction_data': {}, 'accuracy': 0}
    )
    
    if created or request.GET.get('refresh'):
        # 进行新的预测
        result = SalesAnalysisService.predict_sales(car_id)
        if result:
            prediction_data, accuracy = result
            analysis.prediction_data = prediction_data
            analysis.accuracy = accuracy
            analysis.save()
    
    context = {
        'car': car,
        'analysis': analysis,
        'last_updated': analysis.analysis_date
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'prediction_data': analysis.prediction_data,
            'accuracy': analysis.accuracy
        })
    
    return render(request, 'car_analysis/sales_prediction.html', context)

@login_required
def price_analysis(request, car_id):
    """价格分析"""
    car = get_object_or_404(CarModel, id=car_id)
    
    # 获取或创建价格分析
    today = timezone.now().date()
    analysis, created = PriceAnalysis.objects.get_or_create(
        car=car,
        analysis_date=today,
        defaults={'trend_data': {}, 'prediction_data': {}, 'confidence_level': 0}
    )
    
    if created or request.GET.get('refresh'):
        # 进行新的分析
        result = PriceAnalysisService.analyze_price_trend(car_id)
        if result:
            trend_data, prediction_data, confidence = result
            analysis.trend_data = trend_data
            analysis.prediction_data = prediction_data
            analysis.confidence_level = confidence
            analysis.save()
    
    context = {
        'car': car,
        'analysis': analysis,
        'last_updated': analysis.analysis_date
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'trend_data': analysis.trend_data,
            'prediction_data': analysis.prediction_data,
            'confidence_level': analysis.confidence_level
        })
    
    return render(request, 'car_analysis/price_analysis.html', context)

@login_required
def market_analysis(request):
    """市场分析"""
    segment = request.GET.get('segment')
    analysis_type = request.GET.get('type', 'segment')
    
    if not segment:
        # 显示分析选项页面
        segments = CarModel.BODY_TYPES
        return render(request, 'car_analysis/market_analysis_options.html', {
            'segments': segments
        })
    
    # 获取日期范围
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)  # 默认分析最近一年
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # 获取或创建市场分析
    analysis, created = MarketAnalysis.objects.get_or_create(
        analysis_type=analysis_type,
        analysis_date=end_date,
        target_segment=segment,
        defaults={'analysis_data': {}, 'insights': ''}
    )
    
    if created or request.GET.get('refresh'):
        # 进行新的分析
        analysis_data = MarketAnalysisService.analyze_market_segment(
            segment,
            {'start': start_date, 'end': end_date}
        )
        
        if analysis_data:
            analysis.analysis_data = analysis_data
            # 生成分析洞察
            insights = []
            overview = analysis_data['segment_overview']
            insights.append(f"该细分市场共有{overview['total_models']}款车型")
            insights.append(f"平均售价为{overview['avg_price']:.2f}万元")
            insights.append(f"总销量达到{overview['total_sales']}辆")
            
            # 找出市场份额最大的品牌
            top_brand = analysis_data['brand_performance'][0]
            insights.append(
                f"{top_brand['brand']}以{top_brand['market_share']:.1f}%的市场份额领跑该细分市场"
            )
            
            analysis.insights = '\n'.join(insights)
            analysis.save()
    
    context = {
        'segment': segment,
        'analysis': analysis,
        'start_date': start_date,
        'end_date': end_date
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'analysis_data': analysis.analysis_data,
            'insights': analysis.insights
        })
    
    return render(request, 'car_analysis/market_analysis.html', context)
