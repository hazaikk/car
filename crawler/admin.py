from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django.shortcuts import render, redirect
from django.db.models import Avg, Min, Max, Count, Q
from django.utils.html import format_html
from django.contrib import messages
from django.utils import timezone
from django.template.response import TemplateResponse
from django.contrib.admin.views.main import ChangeList
from django.db.models.functions import TruncMonth, TruncYear
from django.core.exceptions import ValidationError
import threading
import pandas as pd
import io
from analysis_records.models import AnalysisRecord # 确保导入

# Register your models here.
# crawler/admin.py
from .models import Brand, CarModel, UsedCar, CrawlerTask
from .crawler_service import CarCrawlerService
from .forms import CrawlerTaskForm

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的品牌数据到Excel"""
        import pandas as pd
        from django.http import HttpResponse
        import io
        
        # 准备数据
        data = []
        for brand in queryset:
            data.append({
                'ID': brand.id,
                '品牌名称': brand.name,
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='品牌数据')
        
        # 返回响应
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="brands_export.xlsx"'
        return response
    
    export_to_excel.short_description = '导出选中的品牌到Excel'

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    list_filter = ('brand',)
    search_fields = ('name', 'brand__name')
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的车型数据到Excel"""
        import pandas as pd
        from django.http import HttpResponse
        import io
        
        # 准备数据
        data = []
        for car_model in queryset:
            data.append({
                'ID': car_model.id,
                '车型名称': car_model.name,
                '品牌': car_model.brand.name,
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='车型数据')
        
        # 返回响应
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="car_models_export.xlsx"'
        return response
    
    export_to_excel.short_description = '导出选中的车型到Excel'

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
    list_display = ('title', 'car_model', 'price', 'first_registration', 'mileage', 'location')
    list_filter = ('car_model__brand', 'first_registration', 'location', 'gearbox', 'fuel_type', 'drive_type', 'emission_standard')
    search_fields = ('title', 'car_model__name', 'car_model__brand__name')
    date_hierarchy = 'created_at'
    change_list_template = 'admin/usedcar_change_list.html'
    actions = ['export_to_excel']
    
    def get_changelist(self, request, **kwargs):
        return UsedCarChangeList
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analysis/', self.admin_site.admin_view(self.analysis_view), name='crawler_usedcar_analysis'),
            path('api/analysis-data/', self.admin_site.admin_view(self.analysis_data_api), name='crawler_usedcar_analysis_data'),
            path('import/', self.admin_site.admin_view(self.import_view), name='crawler_usedcar_import'),
            path('import/upload/', self.admin_site.admin_view(self.import_upload), name='crawler_usedcar_import_upload'),
        ]
        return custom_urls + urls
    

    
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
                {'id': 'count_by_drive_type', 'name': '驱动方式分析'},
            ],
        )
        return TemplateResponse(request, "admin/usedcar_analysis.html", context)
    
    def export_to_excel(self, request, queryset):
        """导出选中的二手车数据到Excel"""
        import pandas as pd
        from django.http import HttpResponse
        import io
        
        # 准备数据
        data = []
        for car in queryset:
            data.append({
                'ID': car.id,
                '车辆标题': car.title,
                '品牌': car.car_model.brand.name if car.car_model and car.car_model.brand else '',
                '车型': car.car_model.name if car.car_model else '',
                '价格(万元)': float(car.price) if car.price else 0,
                '里程': car.mileage or '',
                '所在地': car.location or '',
                '首次上牌': car.first_registration or '',
                '变速箱': car.gearbox or '',
                '燃料类型': car.fuel_type or '',
                '驱动方式': car.drive_type or '',
                '排放标准': car.emission_standard or '',
                '创建时间': car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='二手车数据')
        
        # 返回响应
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="used_cars_export.xlsx"'
        return response
    
    export_to_excel.short_description = '导出选中的二手车到Excel'
    
    def import_view(self, request):
        """显示数据导入页面"""
        context = dict(
            self.admin_site.each_context(request),
            title="导入二手车数据",
        )
        return TemplateResponse(request, "admin/crawler/import_data.html", context)
    
    def import_upload(self, request):
        """处理Excel文件上传和导入"""
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            
            try:
                # 读取Excel文件
                df = pd.read_excel(excel_file)
                
                # 基本字段映射
                field_mapping = {
                    '车辆名称': 'title',
                    '价格': 'price',
                    '详情链接': 'detail_url',
                    '上牌时间': 'first_registration',
                    '表显里程': 'mileage',
                    '变\xa0\xa0速\xa0\xa0箱': 'gearbox',
                    '燃料类型': 'fuel_type',
                    '出险查询': 'accident_check',
                    '年检到期': 'annual_inspection',
                    '保险到期': 'insurance_expiry',
                    '过户次数': 'transfer_count',
                    '所\xa0\xa0在\xa0\xa0地': 'location',
                    '驱动方式': 'drive_type',
                    '排放标准': 'emission_standard',
                    '排\xa0\xa0\xa0\xa0\xa0\xa0\xa0量': 'displacement'
                }
                
                success_count = 0
                error_count = 0
                

                for idx, row in df.iterrows():
                    try:
                        car_data = {}
                        
                        # 处理基本字段
                        for excel_col, model_field in field_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                
                                # 特殊处理所在地字段，不跳过空值检查
                                if model_field == 'location':
                                    # 特殊处理所在地字段，去除空格并确保不为空
                                    if not pd.isna(value) and value != '-':
                                        location_value = str(value).strip()
                                        if location_value:
                                            car_data[model_field] = location_value
                                    continue
                                
                                # 跳过空值和'-'
                                if pd.isna(value) or value == '-' or str(value).strip() == '':
                                    continue
                                
                                # 根据字段类型处理数据
                                if model_field == 'price':
                                    car_data[model_field] = self._parse_price(value)
                                elif model_field == 'mileage':
                                    parsed_mileage = self._parse_mileage(value)
                                    if parsed_mileage is not None:
                                        car_data[model_field] = parsed_mileage
                                        car_data['mileage_text'] = str(value)
                                elif model_field == 'first_registration':
                                    # 处理上牌时间，同时设置first_registration和registration_date
                                    car_data['first_registration'] = str(value)
                                    parsed_date = self._parse_date(str(value))
                                    if parsed_date:
                                        car_data['registration_date'] = parsed_date
                                elif model_field in ['annual_inspection', 'insurance_expiry']:
                                    car_data[model_field] = str(value)
                                elif model_field == 'transfer_count':
                                    parsed_count = self._parse_transfer_count(value)
                                    if parsed_count is not None:
                                        car_data[model_field] = parsed_count
                                else:
                                    car_data[model_field] = str(value)
                        
                        # 处理品牌和车型
                        car_model = None
                        if '车辆名称' in df.columns:
                            title = row['车辆名称']
                            if not pd.isna(title) and str(title).strip():
                                car_data['title'] = str(title)
                                brand_name, model_name = self._clean_brand_model(str(title))
                                
                                # 获取或创建品牌
                                brand, _ = Brand.objects.get_or_create(name=brand_name)
                                
                                # 获取或创建车型
                                car_model, _ = CarModel.objects.get_or_create(
                                    brand=brand,
                                    name=model_name
                                )
                                car_data['car_model'] = car_model
                        
                        # 如果没有车型信息，创建默认的
                        if car_model is None:
                            default_brand, _ = Brand.objects.get_or_create(name='未知品牌')
                            car_model, _ = CarModel.objects.get_or_create(
                                brand=default_brand,
                                name='未知车型'
                            )
                            car_data['car_model'] = car_model
                            if 'title' not in car_data:
                                car_data['title'] = '未知车辆'
                        
                        # 位置信息已在字段映射中处理，这里不需要重复处理
                        
                        # 确保必要字段有默认值
                        if 'price' not in car_data or car_data['price'] is None:
                            car_data['price'] = 0.00
                        
                        # 创建二手车记录
                        UsedCar.objects.create(**car_data)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"导入第{idx+1}行数据失败: {str(e)}")
                        print(f"数据内容: {dict(row)}")
                        print(f"处理后的car_data: {car_data}")
                        continue
                
                messages.success(request, f'导入完成！成功导入 {success_count} 条记录，失败 {error_count} 条记录。')
                
            except Exception as e:
                messages.error(request, f'导入失败：{str(e)}')
            
            return redirect('admin:crawler_usedcar_changelist')
        
        return redirect('admin:crawler_usedcar_import')
    
    def _clean_brand_model(self, title):
        """从车辆名称中提取品牌和车型"""
        parts = title.split(' ', 1)
        if len(parts) < 2:
            return '未知品牌', title
        return parts[0], parts[1]
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str or pd.isna(date_str) or date_str == '-':
            return None
        
        from datetime import datetime
        try:
            # 处理"2019年03月"格式
            if '年' in date_str and '月' in date_str:
                year = int(date_str.split('年')[0])
                month = int(date_str.split('年')[1].split('月')[0])
                return datetime(year, month, 1).date()
            
            # 处理"2026-03"格式
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 2:
                    return datetime(int(parts[0]), int(parts[1]), 1).date()
        except:
            return None
    
    def _parse_mileage(self, mileage_str):
        """解析里程数，返回万公里为单位的数值"""
        if not mileage_str or pd.isna(mileage_str):
            return None
        
        from decimal import Decimal
        try:
            # 处理"6.7万公里"格式，直接提取数值（已经是万公里单位）
            if '万公里' in str(mileage_str):
                value = float(str(mileage_str).replace('万公里', ''))
                return Decimal(str(value))
            # 处理纯数字格式，假设是公里，转换为万公里
            elif str(mileage_str).replace('.', '').isdigit():
                value = float(str(mileage_str)) / 10000
                return Decimal(str(value))
            return None
        except:
            return None
    
    def _parse_price(self, price):
        """解析价格"""
        from decimal import Decimal
        if pd.isna(price):
            return Decimal('0.00')
        try:
            price_str = str(price).strip()
            # 处理包含万元的价格格式
            if '万' in price_str:
                # 提取数字部分
                import re
                numbers = re.findall(r'\d+\.?\d*', price_str)
                if numbers:
                    return Decimal(numbers[0])
            # 处理纯数字
            else:
                # 移除可能的非数字字符
                import re
                clean_price = re.sub(r'[^\d.]', '', price_str)
                if clean_price:
                    return Decimal(clean_price)
            return Decimal('0.00')
        except:
            return Decimal('0.00')
    
    def _parse_transfer_count(self, transfer_str):
        """解析过户次数"""
        if not transfer_str or pd.isna(transfer_str):
            return None
        try:
            # 提取数字
            num = ''.join(filter(str.isdigit, str(transfer_str)))
            return int(num) if num else None
        except:
            return None
    
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
            queryset = queryset.filter(first_registration__icontains=year_from)
        if year_to:
            queryset = queryset.filter(first_registration__icontains=year_to)
        if date_from:
            # 使用解析后的日期字段进行精确筛选
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__gte=date_from_obj)
            except:
                # 如果日期格式不正确，回退到字符串包含查询
                queryset = queryset.filter(first_registration__icontains=date_from)
        if date_to:
            # 使用解析后的日期字段进行精确筛选
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date__lte=date_to_obj)
            except:
                # 如果日期格式不正确，回退到字符串包含查询
                queryset = queryset.filter(first_registration__icontains=date_to)
        if mileage_from:
            # 使用数值字段进行筛选（万公里单位）
            queryset = queryset.filter(mileage__gte=float(mileage_from))
        if mileage_to:
            # 使用数值字段进行筛选（万公里单位）
            queryset = queryset.filter(mileage__lte=float(mileage_to))
        
        # 根据分析类型执行不同的分析
        result = {}
        if analysis_type == 'price_by_brand':
            # 过滤掉价格为空或无效的数据，限制返回数量防止性能问题
            data = queryset.exclude(price__isnull=True).exclude(price__lte=0).values('car_model__brand__name').annotate(
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
                'detailed_data': [{
                    'min_price': float(item['min_price']),
                    'max_price': float(item['max_price']),
                    'car_count': item['car_count']
                } for item in data],
                'title': '品牌平均价格(万元)',
                'type': 'bar'
            }
        
        elif analysis_type == 'price_by_region':
            # 过滤掉价格为空、地区为空或无效的数据，限制返回数量防止性能问题
            data = queryset.exclude(price__isnull=True).exclude(price__lte=0).exclude(location__isnull=True).exclude(location='').values('location').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                car_count=Count('id')
            ).filter(car_count__gte=3).order_by('-avg_price')
            
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
        
        elif analysis_type == 'price_by_year':
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
        
        elif analysis_type == 'price_by_mileage':
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

        # ... (其他分析类型的代码保持不变) ...
        
        elif analysis_type == 'count_by_brand':
            # 过滤掉品牌为空的数据，限制返回数量防止性能问题
            data = queryset.exclude(car_model__brand__name__isnull=True).exclude(car_model__brand__name='').values('car_model__brand__name').annotate(
                car_count=Count('id')
            ).filter(car_count__gt=0).order_by('-car_count')[:30]  # 限制最多30个品牌
            
            result = {
                'labels': [item['car_model__brand__name'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '品牌车辆数量',
                'type': 'bar'
            }
        
        elif analysis_type == 'count_by_region':
            # 过滤掉地区为空的数据，限制返回数量防止性能问题
            data = queryset.exclude(location__isnull=True).exclude(location='').values('location').annotate(
                car_count=Count('id')
            ).filter(car_count__gt=0).order_by('-car_count')[:30]  # 限制最多30个地区
            
            result = {
                'labels': [item['location'] for item in data],
                'regions': [item['location'] for item in data],  # 添加 regions 属性以保持兼容性
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
            data = queryset.exclude(gearbox=None).exclude(gearbox='').values('gearbox').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['gearbox'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '变速箱类型分布',
                'type': 'pie'
            }
        
        elif analysis_type == 'count_by_drive_type':
            data = queryset.exclude(drive_type=None).exclude(drive_type='').values('drive_type').annotate(
                car_count=Count('id')
            ).order_by('-car_count')
            
            result = {
                'labels': [item['drive_type'] for item in data],
                'values': [item['car_count'] for item in data],
                'title': '驱动方式分布',
                'type': 'pie'
            }
        
        else:
            # 默认处理未知的分析类型
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
            'valid_price_count': valid_price_queryset.count(),
            'avg_price': float(valid_price_queryset.aggregate(avg_price=Avg('price'))['avg_price'] or 0),
            'min_price': float(valid_price_queryset.aggregate(min_price=Min('price'))['min_price'] or 0),
            'max_price': float(valid_price_queryset.aggregate(max_price=Max('price'))['max_price'] or 0),
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
                    'first_registration', 'mileage', 'location', 'gearbox', 
                    'fuel_type', 'drive_type', 'emission_standard'
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
        
        # 如果不是导出Excel，返回JSON数据
        return JsonResponse(result)

@admin.register(CrawlerTask)
class CrawlerTaskAdmin(admin.ModelAdmin):
    form = CrawlerTaskForm
    list_display = ('name', 'target_count', 'actual_count', 'status_display', 'page_range_display', 'progress_display', 'created_at', 'created_by', 'action_buttons')
    list_filter = ('status', 'created_at', 'created_by')
    search_fields = ('name', 'created_by__username', 'search_keyword')
    readonly_fields = ('actual_count', 'status', 'start_time', 'end_time', 'error_message', 'progress_percentage', 'crawled_data')
    fields = ('name', 'target_count', 'start_page', 'end_page', 'delay_seconds', 'search_keyword', 'actual_count', 'status', 'start_time', 'end_time', 'error_message')
    
    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，添加帮助文本和验证"""
        form = super().get_form(request, obj, **kwargs)
        
        # 为字段添加帮助文本
        if 'target_count' in form.base_fields:
            form.base_fields['target_count'].help_text = '目标爬取的车辆数量（建议不超过1000）'
            form.base_fields['target_count'].widget.attrs.update({'min': '1', 'max': '1000'})
        
        if 'start_page' in form.base_fields:
            form.base_fields['start_page'].help_text = '爬取起始页码（从1开始）'
            form.base_fields['start_page'].widget.attrs.update({'min': '1'})
        
        if 'end_page' in form.base_fields:
            form.base_fields['end_page'].help_text = '爬取终止页码（必须大于起始页码）'
            form.base_fields['end_page'].widget.attrs.update({'min': '1'})
        
        if 'delay_seconds' in form.base_fields:
            form.base_fields['delay_seconds'].help_text = '每次请求间隔时间（秒），建议1-3秒'
            form.base_fields['delay_seconds'].widget.attrs.update({'min': '0.5', 'max': '10', 'step': '0.5'})
        
        if 'search_keyword' in form.base_fields:
            form.base_fields['search_keyword'].help_text = '搜索关键词（可选），如品牌名称或车型'
        
        return form
    
    actions = ['export_to_excel']
    
    def changelist_view(self, request, extra_context=None):
        """自定义任务列表视图，添加创建任务按钮"""
        extra_context = extra_context or {}
        extra_context['create_task_url'] = 'create-task/'
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-task/', self.admin_site.admin_view(self.create_task_view), name='crawler_crawlertask_create_task'),
            path('<int:task_id>/start/', self.admin_site.admin_view(self.start_crawl_view), name='crawler_crawlertask_start'),
            path('<int:task_id>/import/', self.admin_site.admin_view(self.import_data_view), name='crawler_crawlertask_import'),
            path('<int:task_id>/export/', self.admin_site.admin_view(self.export_data_view), name='crawler_crawlertask_export'),
            path('<int:task_id>/view-data/', self.admin_site.admin_view(self.view_data), name='crawler_crawlertask_view_data'),
            path('progress/<int:task_id>/', self.admin_site.admin_view(self.get_task_progress), name='crawler_crawlertask_progress'),
        ]
        return custom_urls + urls
    
    def page_range_display(self, obj):
        """显示页码范围"""
        if obj.end_page:
            page_info = f"{obj.start_page}-{obj.end_page}页"
        else:
            page_info = f"从{obj.start_page}页开始"
        
        if obj.search_keyword:
            page_info += f"<br><small>关键词: {obj.search_keyword}</small>"
        
        page_info += f"<br><small>间隔: {obj.delay_seconds}秒</small>"
        
        return format_html(page_info)
    page_range_display.short_description = '爬取范围'
    
    def progress_display(self, obj):
        """显示进度条"""
        percentage = obj.progress_percentage
        progress_html = f'''
        <div data-task-id="{obj.id}" data-status="{obj.status}">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percentage}%;"></div>
            </div>
            <div class="progress-text">{obj.actual_count}/{obj.target_count} ({percentage:.1f}%)</div>
            <div class="real-time-info">最后更新: {timezone.now().strftime('%H:%M:%S')}</div>
        </div>
        '''
        return format_html(progress_html)
    progress_display.short_description = '进度'
    
    def status_display(self, obj):
        """显示状态"""
        status_class = f'status-{obj.status}'
        return format_html(f'<span class="task-status {status_class}">{obj.get_status_display()}</span>')
    status_display.short_description = '状态'
    
    def action_buttons(self, obj):
        """自定义操作按钮"""
        buttons = []
        
        if obj.status == 'pending':
            buttons.append(
                f'<a class="button" href="{obj.id}/start/" style="background-color: #28a745; color: white !important; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">开始爬取</a>'
            )
        
        if obj.status == 'completed' and obj.crawled_data:
            buttons.append(
                f'<a class="button" href="{obj.id}/view-data/" style="background-color: #17a2b8; color: white !important; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">查看数据</a>'
            )
            buttons.append(
                f'<a class="button" href="{obj.id}/import/" style="background-color: #007bff; color: white !important; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">导入数据库</a>'
            )
            buttons.append(
                f'<a class="button" href="{obj.id}/export/" style="background-color: #6c757d; color: white !important; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">导出Excel</a>'
            )
        
        return format_html(''.join(buttons))
    action_buttons.short_description = '操作'
    
    def create_task_view(self, request):
        """创建爬虫任务视图"""
        if request.method == 'POST':
            name = request.POST.get('name')
            target_count = int(request.POST.get('target_count', 100))
            start_page = int(request.POST.get('start_page', 1))
            end_page = request.POST.get('end_page')
            delay_seconds = float(request.POST.get('delay_seconds', 2.0))
            search_keyword = request.POST.get('search_keyword', '').strip()
            
            # 处理终止页码
            end_page = int(end_page) if end_page and end_page.strip() else None
            
            task = CrawlerTask.objects.create(
                name=name,
                target_count=target_count,
                start_page=start_page,
                end_page=end_page,
                delay_seconds=delay_seconds,
                search_keyword=search_keyword if search_keyword else None,
                created_by=request.user
            )
            
            messages.success(request, f'爬虫任务 "{name}" 创建成功！')
            return redirect('admin:crawler_crawlertask_changelist')
        
        context = {
            'title': '创建爬虫任务',
            'opts': self.model._meta,
        }
        return render(request, 'admin/crawler/create_task.html', context)
    
    def start_crawl_view(self, request, task_id):
        """开始爬取"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            if task.status != 'pending':
                messages.error(request, '只能启动等待中的任务！')
                return redirect('admin:crawler_crawlertask_changelist')
            
            # 在后台线程中启动爬虫
            crawler_service = CarCrawlerService()
            
            def run_crawler():
                crawler_service.crawl_cars(task_id, task.target_count)
            
            thread = threading.Thread(target=run_crawler)
            thread.daemon = True
            thread.start()
            
            messages.success(request, f'爬虫任务 "{task.name}" 已开始运行！')
            
        except CrawlerTask.DoesNotExist:
            messages.error(request, '任务不存在！')
        
        return redirect('admin:crawler_crawlertask_changelist')
    
    def import_data_view(self, request, task_id):
        """导入数据到数据库"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            if task.status != 'completed':
                messages.error(request, '只能导入已完成的任务数据！')
                return redirect('admin:crawler_crawlertask_changelist')
            
            crawler_service = CarCrawlerService()
            success, message = crawler_service.import_to_database(task_id)
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, f'导入失败: {message}')
                
        except CrawlerTask.DoesNotExist:
            messages.error(request, '任务不存在！')
        
        return redirect('admin:crawler_crawlertask_changelist')
    
    def get_task_progress(self, request, task_id):
        """获取任务进度的API接口"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            progress_data = {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'status_display': task.get_status_display(),
                'target_count': task.target_count,
                'actual_count': task.actual_count,
                'progress_percentage': task.progress_percentage,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'error_message': task.error_message,
                'created_at': task.created_at.isoformat(),
            }
            return JsonResponse(progress_data)
        except CrawlerTask.DoesNotExist:
            return JsonResponse({'error': '任务不存在'}, status=404)
    
    def export_data_view(self, request, task_id):
        """导出数据到Excel"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            if not task.crawled_data:
                messages.error(request, '没有可导出的数据！')
                return redirect('admin:crawler_crawlertask_changelist')
            
            # 创建DataFrame
            df = pd.DataFrame(task.crawled_data)
            
            # 创建Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='爬取数据', index=False)
            
            output.seek(0)
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{task.name}_爬取数据.xlsx"'
            return response
            
        except CrawlerTask.DoesNotExist:
            messages.error(request, '任务不存在！')
            return redirect('admin:crawler_crawlertask_changelist')
    
    def view_data(self, request, task_id):
        """查看爬取的数据"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            context = {
                'title': f'查看爬取数据 - {task.name}',
                'task': task,
                'data': task.crawled_data[:100] if task.crawled_data else [],  # 只显示前100条
                'total_count': len(task.crawled_data) if task.crawled_data else 0,
                'opts': self.model._meta,
            }
            return render(request, 'admin/crawler/view_data.html', context)
            
        except CrawlerTask.DoesNotExist:
            messages.error(request, '任务不存在！')
            return redirect('admin:crawler_crawlertask_changelist')
    
    def export_to_excel(self, request, queryset):
        """批量导出任务到Excel"""
        data = []
        for task in queryset:
            data.append({
                '任务名称': task.name,
                '目标数量': task.target_count,
                '实际数量': task.actual_count,
                '状态': task.get_status_display(),
                '创建者': task.created_by.username,
                '创建时间': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '开始时间': task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else '',
                '结束时间': task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else '',
                '错误信息': task.error_message or '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='爬虫任务', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="爬虫任务列表.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建时
            obj.created_by = request.user
        super().save_model(request, obj, form, change)