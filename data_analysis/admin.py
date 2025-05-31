from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
import pandas as pd
import io
from .models import PriceAnalysisResult, BrandAnalysisResult, RegionAnalysisResult, VehicleAttributeAnalysisResult

# 注册数据分析模型到后台管理界面
@admin.register(PriceAnalysisResult)
class PriceAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的价格分析结果到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '分析类型': obj.analysis_type or '',
                '分析日期': obj.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if obj.analysis_date else '',
                '摘要': obj.summary or '',
                '详细结果': str(obj.result_data) if obj.result_data else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='价格分析结果', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="价格分析结果.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(BrandAnalysisResult)
class BrandAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的品牌分析结果到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '分析类型': obj.analysis_type or '',
                '分析日期': obj.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if obj.analysis_date else '',
                '摘要': obj.summary or '',
                '详细结果': str(obj.result_data) if obj.result_data else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='品牌分析结果', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="品牌分析结果.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(RegionAnalysisResult)
class RegionAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的地区分析结果到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '分析类型': obj.analysis_type or '',
                '分析日期': obj.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if obj.analysis_date else '',
                '摘要': obj.summary or '',
                '详细结果': str(obj.result_data) if obj.result_data else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='地区分析结果', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="地区分析结果.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"

@admin.register(VehicleAttributeAnalysisResult)
class VehicleAttributeAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'
    actions = ['export_to_excel']
    
    def export_to_excel(self, request, queryset):
        """导出选中的车辆属性分析结果到Excel"""
        data = []
        for obj in queryset:
            data.append({
                '分析类型': obj.analysis_type or '',
                '分析日期': obj.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if obj.analysis_date else '',
                '摘要': obj.summary or '',
                '详细结果': str(obj.result_data) if obj.result_data else '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='车辆属性分析结果', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="车辆属性分析结果.xlsx"'
        return response
    
    export_to_excel.short_description = "导出选中项到Excel"
