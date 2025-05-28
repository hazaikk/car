from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from dashboard.models import CarModel
from .models import SalesAnalysis, PriceAnalysis, MarketAnalysis
from .services import SalesAnalysisService, PriceAnalysisService, MarketAnalysisService

# Create your views here.

@login_required
def index(request):
    """智能分析首页"""
    return render(request, 'car_analysis/index.html')

@login_required
def comparison(request):
    """竞品对比页面"""
    return render(request, 'car_analysis/comparison.html')

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
