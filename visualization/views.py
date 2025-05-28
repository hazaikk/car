from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Chart, Dashboard, DashboardChart
from dashboard.models import Brand, CarModel, PriceHistory, SalesData, UserRating
import json

def chart_list(request):
    """显示所有公开的图表列表"""
    charts = Chart.objects.filter(is_public=True).order_by('-created_at')
    return render(request, 'visualization/chart_list.html', {
        'charts': charts
    })

@login_required
def my_charts(request):
    """显示用户创建的图表"""
    charts = Chart.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'visualization/my_charts.html', {
        'charts': charts
    })

@login_required
def chart_create(request):
    """创建新图表"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chart = Chart.objects.create(
                title=data['title'],
                description=data.get('description'),
                chart_type=data['chart_type'],
                data_type=data['data_type'],
                config=data.get('config', {}),
                created_by=request.user,
                is_public=data.get('is_public', True)
            )
            return JsonResponse({'success': True, 'chart_id': chart.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # 获取可用的数据字段
    fields = {
        'sales': [
            {'value': 'month', 'label': '月份'},
            {'value': 'sales_volume', 'label': '销量'},
        ],
        'price': [
            {'value': 'date', 'label': '日期'},
            {'value': 'price', 'label': '价格'},
        ],
        'rating': [
            {'value': 'created_at', 'label': '评价时间'},
            {'value': 'overall_rating', 'label': '综合评分'},
            {'value': 'exterior_rating', 'label': '外观评分'},
            {'value': 'interior_rating', 'label': '内饰评分'},
            {'value': 'configuration_rating', 'label': '配置评分'},
            {'value': 'performance_rating', 'label': '性能评分'},
            {'value': 'comfort_rating', 'label': '舒适度评分'},
            {'value': 'cost_performance_rating', 'label': '性价比评分'},
        ],
    }
    
    return render(request, 'visualization/chart_create.html', {
        'fields': fields,
        'chart_types': Chart.CHART_TYPES,
        'data_types': Chart.DATA_TYPES,
    })

@login_required
def chart_edit(request, chart_id):
    """编辑图表"""
    chart = get_object_or_404(Chart, id=chart_id)
    if chart.created_by != request.user:
        messages.error(request, '您没有权限编辑此图表')
        return redirect('visualization:chart_list')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chart.title = data['title']
            chart.description = data.get('description')
            chart.chart_type = data['chart_type']
            chart.data_type = data['data_type']
            chart.config = data.get('config', {})
            chart.is_public = data.get('is_public', True)
            chart.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'visualization/chart_edit.html', {
        'chart': chart
    })

def chart_detail(request, chart_id):
    """查看图表详情"""
    chart = get_object_or_404(Chart, id=chart_id)
    if not chart.is_public and (not request.user.is_authenticated or chart.created_by != request.user):
        messages.error(request, '您没有权限查看此图表')
        return redirect('visualization:chart_list')
    
    return render(request, 'visualization/chart_detail.html', {
        'chart': chart
    })

@login_required
def chart_data(request, chart_id):
    """获取图表数据"""
    chart = get_object_or_404(Chart, id=chart_id)
    if not chart.is_public and chart.created_by != request.user:
        return JsonResponse({'error': '没有权限'}, status=403)
    
    # 获取筛选参数
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    brand_id = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    region = request.GET.get('region')
    
    # 根据图表类型和数据类型获取数据
    data = {'labels': [], 'datasets': []}
    
    if chart.data_type == 'sales':
        # 销量数据
        sales_data = SalesData.objects.all()
        if start_date:
            sales_data = sales_data.filter(month__gte=start_date)
        if end_date:
            sales_data = sales_data.filter(month__lte=end_date)
        if brand_id:
            sales_data = sales_data.filter(car__brand_id=brand_id)
            
        if chart.chart_type == 'line':
            # 按月份统计销量趋势
            sales_by_month = sales_data.values('month').annotate(
                total_sales=Sum('sales_volume')
            ).order_by('month')
            
            data['labels'] = [item['month'].strftime('%Y-%m') for item in sales_by_month]
            data['datasets'].append({
                'label': '销量',
                'data': [item['total_sales'] for item in sales_by_month],
                'fill': False
            })
            
        elif chart.chart_type == 'pie':
            # 按品牌统计销量占比
            sales_by_brand = sales_data.values('car__brand__name').annotate(
                total_sales=Sum('sales_volume')
            ).order_by('-total_sales')
            
            data['labels'] = [item['car__brand__name'] for item in sales_by_brand]
            data['datasets'].append({
                'data': [item['total_sales'] for item in sales_by_brand]
            })
    
    elif chart.data_type == 'price':
        # 价格数据
        price_data = PriceHistory.objects.all()
        if start_date:
            price_data = price_data.filter(date__gte=start_date)
        if end_date:
            price_data = price_data.filter(date__lte=end_date)
        if brand_id:
            price_data = price_data.filter(car__brand_id=brand_id)
        if min_price:
            price_data = price_data.filter(price__gte=float(min_price))
        if max_price:
            price_data = price_data.filter(price__lte=float(max_price))
            
        if chart.chart_type == 'line':
            # 价格趋势
            price_trend = price_data.values('date').annotate(
                avg_price=Avg('price')
            ).order_by('date')
            
            data['labels'] = [item['date'].strftime('%Y-%m-%d') for item in price_trend]
            data['datasets'].append({
                'label': '平均价格',
                'data': [float(item['avg_price']) for item in price_trend],
                'fill': False
            })
            
        elif chart.chart_type == 'bar':
            # 价格区间分布
            ranges = [
                (0, 5), (5, 10), (10, 15), (15, 20),
                (20, 30), (30, 50), (50, float('inf'))
            ]
            labels = ['0-5万', '5-10万', '10-15万', '15-20万',
                     '20-30万', '30-50万', '50万以上']
            counts = []
            
            for start, end in ranges:
                count = price_data.filter(price__gte=start)
                if end != float('inf'):
                    count = count.filter(price__lt=end)
                counts.append(count.count())
            
            data['labels'] = labels
            data['datasets'].append({
                'label': '车型数量',
                'data': counts
            })
    
    elif chart.data_type == 'rating':
        # 评分数据
        rating_data = UserRating.objects.all()
        if start_date:
            rating_data = rating_data.filter(created_at__date__gte=start_date)
        if end_date:
            rating_data = rating_data.filter(created_at__date__lte=end_date)
        if brand_id:
            rating_data = rating_data.filter(car__brand_id=brand_id)
            
        if chart.chart_type == 'radar':
            # 各维度评分
            avg_ratings = rating_data.aggregate(
                exterior=Avg('exterior_rating'),
                interior=Avg('interior_rating'),
                config=Avg('configuration_rating'),
                performance=Avg('performance_rating'),
                comfort=Avg('comfort_rating'),
                cost_performance=Avg('cost_performance_rating')
            )
            
            data['labels'] = ['外观', '内饰', '配置', '性能', '舒适度', '性价比']
            data['datasets'].append({
                'label': '平均评分',
                'data': [
                    float(avg_ratings['exterior'] or 0),
                    float(avg_ratings['interior'] or 0),
                    float(avg_ratings['config'] or 0),
                    float(avg_ratings['performance'] or 0),
                    float(avg_ratings['comfort'] or 0),
                    float(avg_ratings['cost_performance'] or 0)
                ]
            })
            
        elif chart.chart_type == 'bar':
            # 评分分布
            rating_dist = rating_data.values('overall_rating').annotate(
                count=Count('id')
            ).order_by('overall_rating')
            
            data['labels'] = [f"{float(item['overall_rating'])}分" for item in rating_dist]
            data['datasets'].append({
                'label': '评分分布',
                'data': [item['count'] for item in rating_dist]
            })
    
    return JsonResponse(data)

def dashboard_list(request):
    """显示所有公开的仪表盘列表"""
    dashboards = Dashboard.objects.filter(is_public=True).order_by('-created_at')
    return render(request, 'visualization/dashboard_list.html', {
        'dashboards': dashboards
    })

@login_required
def my_dashboards(request):
    """显示用户创建的仪表盘"""
    dashboards = Dashboard.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'visualization/my_dashboards.html', {
        'dashboards': dashboards
    })

@login_required
def dashboard_create(request):
    """创建新仪表盘"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dashboard = Dashboard.objects.create(
                title=data['title'],
                description=data.get('description'),
                created_by=request.user,
                is_public=data.get('is_public', True)
            )
            
            # 添加图表到仪表盘
            charts_data = data.get('charts', [])
            for chart_data in charts_data:
                DashboardChart.objects.create(
                    dashboard=dashboard,
                    chart_id=chart_data['chart_id'],
                    position_x=chart_data.get('position_x', 0),
                    position_y=chart_data.get('position_y', 0),
                    width=chart_data.get('width', 6),
                    height=chart_data.get('height', 4)
                )
            return JsonResponse({'success': True, 'dashboard_id': dashboard.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # 获取用户可用的图表
    available_charts = Chart.objects.filter(
        models.Q(is_public=True) | models.Q(created_by=request.user)
    ).order_by('-created_at')
    
    return render(request, 'visualization/dashboard_create.html', {
        'available_charts': available_charts
    })

def dashboard_detail(request, dashboard_id):
    """查看仪表盘详情"""
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
    if not dashboard.is_public and (not request.user.is_authenticated or dashboard.created_by != request.user):
        messages.error(request, '您没有权限查看此仪表盘')
        return redirect('visualization:dashboard_list')
    
    dashboard_charts = DashboardChart.objects.filter(dashboard=dashboard).select_related('chart')
    return render(request, 'visualization/dashboard_detail.html', {
        'dashboard': dashboard,
        'dashboard_charts': dashboard_charts
    })
