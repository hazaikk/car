from django.contrib import admin
from django.http import JsonResponse
from django.db.models import Avg, Count, Min, Max, Sum
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django.db.models.functions import TruncMonth, TruncYear
from analysis_records.models import AnalysisRecord # 确保导入

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
        
        # 处理获取地区数据的请求
        if analysis_type == 'get_regions':
            # 获取所有不重复的地区
            regions_list = UsedCar.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
            return JsonResponse({'regions': list(regions_list)})
            
        brand_ids = request.GET.getlist('brands', [])
        regions = request.GET.getlist('regions', [])
        year_from = request.GET.get('year_from')
        year_to = request.GET.get('year_to')
        date_from = request.GET.get('registration_date_from')
        date_to = request.GET.get('registration_date_to')
        mileage_from = request.GET.get('mileage_from')
        mileage_to = request.GET.get('mileage_to')
        export_to_excel = request.GET.get('export_to_excel', 'false').lower() == 'true'
        
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
        if date_from:
            queryset = queryset.filter(registration_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(registration_date__lte=date_to)
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

        # ... (其他分析类型的代码保持不变) ...
        
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

        if export_to_excel:
            import pandas as pd
            from django.http import HttpResponse
            import io

            # 将查询结果转换为DataFrame
            # 注意：这里的字段需要根据实际分析类型动态调整，或者提供一个通用的导出格式
            # 为简化示例，我们假设导出的是当前筛选条件下的原始数据列表
            # 更完善的实现应该根据 analysis_type 导出对应分析结果的表格数据
            
            if analysis_type == 'price_by_brand' and 'labels' in result:
                df_data = {
                    '品牌': result['labels'],
                    '平均价格(万元)': result['values'],
                    '最低价格(万元)': result['min_values'],
                    '最高价格(万元)': result['max_values'],
                    '车辆数量': result['counts'],
                }
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
            elif analysis_type == 'price_by_region' and 'labels' in result:
                df_data = {
                    '地区': result['labels'],
                    '平均价格(万元)': result['values'],
                    '最低价格(万元)': result['min_values'],
                    '最高价格(万元)': result['max_values'],
                    '车辆数量': result['counts'],
                }
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
            elif analysis_type == 'price_by_year' and 'labels' in result:
                df_data = {
                    '年份': result['labels'],
                    '平均价格(万元)': result['values'],
                    '最低价格(万元)': result['min_values'],
                    '最高价格(万元)': result['max_values'],
                    '车辆数量': result['counts'],
                }
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
            elif analysis_type == 'price_by_mileage' and 'labels' in result:
                df_data = {
                    '里程范围': result['labels'],
                    '平均价格(万元)': result['values'],
                    '最低价格(万元)': result['min_values'],
                    '最高价格(万元)': result['max_values'],
                    '车辆数量': result['counts'],
                }
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
            elif analysis_type.startswith('count_') and 'labels' in result:
                # 获取总数用于计算占比
                total_count_for_percentage = sum(result['values'])
                percentages = [(val / total_count_for_percentage * 100) if total_count_for_percentage > 0 else 0 for val in result['values']]
                df_data = {
                    result.get('title').split(' ')[0] if result.get('title') else '类别': result['labels'], # 例如：品牌, 地区
                    '数量': result['values'],
                    '占比(%)': [f"{p:.2f}%" for p in percentages]
                }
                df = pd.DataFrame(df_data)
                filename = f"{result.get('title', 'export')}.xlsx"
            else:
                # 通用导出，导出筛选后的原始数据
                data_list = list(queryset.values(
                    'title', 'car_model__brand__name', 'car_model__name', 'price', 
                    'registration_date', 'mileage', 'location', 'transmission', 
                    'fuel_type', 'color', 'emission_standard'
                ))
                df = pd.DataFrame(data_list)
                filename = "filtered_used_cars_data.xlsx"

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='AnalysisData')
            
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        # 保存分析记录
        if not export_to_excel and request.user.is_authenticated:
            from analysis_records.models import AnalysisRecord
            # 为了简化，参数直接保存GET请求的字典，结果摘要可以是图表的标题或部分数据
            record_params = dict(request.GET)
            # 移除可能存在的敏感信息或过大的数据，例如文件内容
            if 'csrfmiddlewaretoken' in record_params: # 示例，实际情况可能不同
                del record_params['csrfmiddlewaretoken']

            summary_for_record = result.get('title', '未知分析')
            if 'labels' in result and 'values' in result and len(result['labels']) > 0:
                summary_for_record += f" - {result['labels'][0]}: {result['values'][0]}"
                if len(result['labels']) > 1:
                    summary_for_record += "...等"
            
            AnalysisRecord.objects.create(
                user=request.user,
                analysis_type=analysis_type,
                parameters=record_params,
                result_summary=summary_for_record
            )

        return JsonResponse(result)