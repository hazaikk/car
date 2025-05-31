from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
import pandas as pd
import io
from .models import Brand, CarModel, PriceHistory, SalesData, UserRating

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的品牌数据到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '品牌名称': obj.name,
                '描述': obj.description or '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='品牌数据', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="品牌数据.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'body_type', 'price_range', 'launch_date', 'is_listed')
    list_filter = ('brand', 'body_type', 'is_listed')
    search_fields = ('name', 'brand__name')
    date_hierarchy = 'launch_date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的车型数据到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '品牌': obj.brand.name if obj.brand else '',
                '车型名称': obj.name,
                '车身类型': obj.body_type or '',
                '价格区间': obj.price_range or '',
                '上市日期': obj.launch_date.strftime('%Y-%m-%d') if obj.launch_date else '',
                '是否在售': '是' if obj.is_listed else '否',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='车型数据', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="车型数据.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('car', 'price', 'date')
    list_filter = ('car__brand', 'date')
    search_fields = ('car__name', 'car__brand__name')
    date_hierarchy = 'date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的价格历史数据到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '车型': obj.car.name if obj.car else '',
                '品牌': obj.car.brand.name if obj.car and obj.car.brand else '',
                '价格(万元)': float(obj.price) if obj.price else 0,
                '日期': obj.date.strftime('%Y-%m-%d') if obj.date else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='价格历史', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="价格历史数据.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(SalesData)
class SalesDataAdmin(admin.ModelAdmin):
    list_display = ('car', 'month', 'sales_volume')
    list_filter = ('car__brand', 'month')
    search_fields = ('car__name', 'car__brand__name')
    date_hierarchy = 'month'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的销售数据到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '车型': obj.car.name if obj.car else '',
                '品牌': obj.car.brand.name if obj.car and obj.car.brand else '',
                '月份': obj.month.strftime('%Y-%m') if obj.month else '',
                '销量': obj.sales_volume or 0,
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='销售数据', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="销售数据.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('car', 'overall_rating', 'created_at')
    list_filter = ('car__brand', 'created_at')
    search_fields = ('car__name', 'car__brand__name', 'comment')
    date_hierarchy = 'created_at'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的用户评价数据到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '车型': obj.car.name if obj.car else '',
                '品牌': obj.car.brand.name if obj.car and obj.car.brand else '',
                '综合评分': obj.overall_rating or 0,
                '评价内容': obj.comment or '',
                '创建时间': obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='用户评价', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="用户评价数据.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"
