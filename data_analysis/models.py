from django.db import models
from django.utils import timezone
from crawler.models import Brand, CarModel, UsedCar

class PriceAnalysisResult(models.Model):
    """价格分析结果"""
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    analysis_type = models.CharField(max_length=50, verbose_name='分析类型',
                                   choices=[
                                       ('brand_price', '品牌价格分析'),
                                       ('region_price', '地区价格分析'),
                                       ('year_price', '年份价格分析'),
                                       ('mileage_price', '里程价格分析'),
                                   ])
    result_data = models.JSONField(verbose_name='分析结果数据')
    summary = models.TextField(verbose_name='分析摘要', blank=True, null=True)
    
    class Meta:
        verbose_name = '价格分析结果'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date}"

class BrandAnalysisResult(models.Model):
    """品牌分析结果"""
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    analysis_type = models.CharField(max_length=50, verbose_name='分析类型',
                                   choices=[
                                       ('brand_popularity', '品牌流行度分析'),
                                       ('brand_price_range', '品牌价格区间分析'),
                                       ('brand_region_distribution', '品牌地区分布分析'),
                                   ])
    result_data = models.JSONField(verbose_name='分析结果数据')
    summary = models.TextField(verbose_name='分析摘要', blank=True, null=True)
    
    class Meta:
        verbose_name = '品牌分析结果'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date}"

class RegionAnalysisResult(models.Model):
    """地区分析结果"""
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    analysis_type = models.CharField(max_length=50, verbose_name='分析类型',
                                   choices=[
                                       ('region_car_count', '地区车辆数量分析'),
                                       ('region_price_level', '地区价格水平分析'),
                                       ('region_brand_preference', '地区品牌偏好分析'),
                                   ])
    result_data = models.JSONField(verbose_name='分析结果数据')
    summary = models.TextField(verbose_name='分析摘要', blank=True, null=True)
    
    class Meta:
        verbose_name = '地区分析结果'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date}"

class VehicleAttributeAnalysisResult(models.Model):
    """车辆属性分析结果"""
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    analysis_type = models.CharField(max_length=50, verbose_name='分析类型',
                                   choices=[
                                       ('fuel_type_analysis', '燃料类型分析'),
                                       ('transmission_analysis', '变速箱类型分析'),
                                       ('color_preference', '颜色偏好分析'),
                                       ('engine_type_analysis', '发动机类型分析'),
                                       ('mileage_distribution', '里程分布分析'),
                                   ])
    result_data = models.JSONField(verbose_name='分析结果数据')
    summary = models.TextField(verbose_name='分析摘要', blank=True, null=True)
    
    class Meta:
        verbose_name = '车辆属性分析结果'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date}"
