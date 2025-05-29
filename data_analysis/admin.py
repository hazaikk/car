from django.contrib import admin
from .models import PriceAnalysisResult, BrandAnalysisResult, RegionAnalysisResult, VehicleAttributeAnalysisResult

# 注册数据分析模型到后台管理界面
@admin.register(PriceAnalysisResult)
class PriceAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'

@admin.register(BrandAnalysisResult)
class BrandAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'

@admin.register(RegionAnalysisResult)
class RegionAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'

@admin.register(VehicleAttributeAnalysisResult)
class VehicleAttributeAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'analysis_date', 'summary')
    list_filter = ('analysis_type', 'analysis_date')
    search_fields = ('analysis_type', 'summary')
    date_hierarchy = 'analysis_date'
