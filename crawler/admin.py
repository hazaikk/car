from django.contrib import admin
from django.http import JsonResponse
from django.db.models import Avg, Count, Min, Max, Sum
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django.db.models.functions import TruncMonth, TruncYear

# Register your models here.
# crawler/admin.py
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

class UsedCarChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super().get_results(*args, **kwargs)
        # 计算统计数据
        self.avg_price = self.queryset.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        self.total_count = self.queryset.count()
        self.min_price = self.queryset.aggregate(min_price=Min('price'))['min_price'] or 0
        self.max_price = self.queryset.aggregate(max_price=Max('price'))['max_price'] or 0

@admin.register(UsedCar)
class UsedCarAdmin(admin.ModelAdmin):
    list_display = ('title', 'car_model', 'price', 'registration_date', 'mileage', 'location', 'view_analysis_button')
    list_filter = ('car_model__brand', 'registration_date', 'location', 'transmission', 'fuel_type', 'color', 'drive_type', 'emission_standard')
    search_fields = ('title', 'car_model__name', 'car_model__brand__name')
    date_hierarchy = 'created_at'
    change_list_template = 'admin/usedcar_change_list.html'
    
    def get_changelist(self, request, **kwargs):
        return UsedCarChangeList
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analysis/', self.admin_site.admin_view(self.analysis_view), name='crawler_usedcar_analysis'),
            path('api/analysis-data/', self.admin_site.admin_view(self.analysis_data_api), name='crawler_usedcar_analysis_data'),
        ]
        return custom_urls + urls
    
    def view_analysis_button(self, obj):
        return format_html(
            '<a class="button" href="{}?id={}">分析</a>',
            '../analysis/',
            obj.id
        )
    view_analysis_button.short_description = '数据分析'
    view_analysis_button.allow_tags = True
    
    def analysis_view(self, request):
        # 获取筛选条件
        context = dict(
            self.admin_site.each_context(request),
            title="二手车数据交互式分析",
            brands=Brand.objects.all(),
            analysis_types=[
                {'id': 'price_by_brand', 'name': '品牌价格分析'},
                {'id': 'price_by_region', 'name': '地区价格分析'},
                {'id': 'price_by_year', 'name': '年份价格分析'},
                {'id': 'price_by_mileage', 'name': '里程价格分析'},
                {'id': 'count_by_brand', 'name': '品牌数量分析'},
                {'id': 'count_by_region', 'name': '地区数量分析'},
                {'id': 'count_by_fuel', 'name': '燃料类型分析'},
                {'id': 'count_by_transmission', 'name': '变速箱类型分析'},
                {'id': 'count_by_color', 'name': '车身颜色分析'},
            ],
        )
        return TemplateResponse(request, "admin/usedcar_analysis.html", context)
    
    def analysis_data_api(self, request):
        # 获取筛选条件
        analysis_type = request.GET.get('type', 'price_by_brand')
        brand_ids = request.GET.getlist('brands', [])
        regions = request.GET.getlist('regions', [])
        year_from = request.GET.get('year_from')
        year_to = request.GET.get('year_to')
        mileage_from = request.GET.get('mileage_from')
        mileage_to = request.GET.get('mileage_to')
        
        # 构建基础查询集
        queryset = UsedCar.objects.all()
        
        # 应用筛选条件
        if brand_ids:
            queryset = queryset.filter(car_model__brand__id__in=brand_ids)
        if regions:
            queryset = queryset.filter(location__in=regions)
        if year_from:
            queryset = queryset.filter(registration_date__year__gte=year_from)
        if year_to:
            queryset = queryset.filter(registration_date__year__lte=year_to)
        if mileage_from:
            queryset = queryset.filter(mileage__gte=float(mileage_from))
        if mileage_to:
            queryset = queryset.filter(mileage__lte=float(mileage_to))
        
        # 根据分析类型执行不同的分析
        result = {}
        if analysis_type == 'price_by_brand':
            data = queryset.values('car_model__brand__name').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('-avg_price')
            
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
            data = queryset.values('location').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('-avg_price')
            
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
            data = queryset.exclude(registration_date=None).values('registration_date__year').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('registration_date__year')
            
            result = {
                'labels': [str(item['registration_date__year']) for item in data],
                'values': [float(item['avg_price']) for item in data],
                'min_values': [float(item['min_price']) for item in data],
                'max_values': [float(item['max_price']) for item in data],
                'counts': [item['car_count'] for item in data],
                'title': '年份平均价格(万元)',
                'type': 'line'
            }
        
        elif analysis_type == 'price_by_mileage':
            # 创建里程范围
            ranges = [(0, 2), (2, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 100)]
            data = []
            
            for i, (start, end) in enumerate(ranges):
                range_data = queryset.filter(mileage__gte=start, mileage__lt=end).aggregate(
                    avg_price=Avg('price'),
                    min_price=Min('price'),
                    max_price=Max('price'),
                    car_count=Count('id')
                )
                
                if range_data['car_count'] > 0:
                    data.append({
                        'range': f"{start}-{end}万公里",
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
            data = queryset.values('car_model__brand__name').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['car_model__brand__name'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '品牌车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'count_by_region':
            data = queryset.values('location').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['location'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '地区车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'count_by_fuel':
            data = queryset.exclude(fuel_type=None).exclude(fuel_type='').values('fuel_type').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['fuel_type'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '燃料类型分布',
                'type': 'pie'
            }
        
        elif analysis_type == 'count_by_transmission':
            data = queryset.exclude(transmission=None).exclude(transmission='').values('transmission').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['transmission'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '变速箱类型分布',
                'type': 'pie'
            }
        
        elif analysis_type == 'count_by_color':
            data = queryset.exclude(color=None).exclude(color='').values('color').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['color'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '车身颜色分布',
                'type': 'pie'
            }
        
        # 添加统计摘要
        result['summary'] = {
            'total_count': queryset.count(),
            'avg_price': float(queryset.aggregate(avg_price=Avg('price'))['avg_price'] or 0),
            'min_price': float(queryset.aggregate(min_price=Min('price'))['min_price'] or 0),
            'max_price': float(queryset.aggregate(max_price=Max('price'))['max_price'] or 0),
        }
        
        return JsonResponse(result)