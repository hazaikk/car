from django.db import models
from django.utils import timezone
from dashboard.models import CarModel

class SalesAnalysis(models.Model):
    """销量分析"""
    car = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name='车型')
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    prediction_data = models.JSONField(verbose_name='预测数据')  # 存储预测结果
    accuracy = models.FloatField(verbose_name='预测准确度')
    
    class Meta:
        verbose_name = '销量分析'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
        unique_together = ['car', 'analysis_date']
    
    def __str__(self):
        return f"{self.car} - {self.analysis_date} 销量分析"

class PriceAnalysis(models.Model):
    """价格分析"""
    car = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name='车型')
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    trend_data = models.JSONField(verbose_name='趋势数据')  # 存储趋势分析结果
    prediction_data = models.JSONField(verbose_name='预测数据')  # 存储预测结果
    confidence_level = models.FloatField(verbose_name='置信度')
    
    class Meta:
        verbose_name = '价格分析'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
        unique_together = ['car', 'analysis_date']
    
    def __str__(self):
        return f"{self.car} - {self.analysis_date} 价格分析"

class MarketAnalysis(models.Model):
    """市场分析"""
    ANALYSIS_TYPES = (
        ('segment', '细分市场分析'),
        ('competition', '竞争态势分析'),
        ('trend', '市场趋势分析'),
    )
    
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES, verbose_name='分析类型')
    analysis_date = models.DateField(default=timezone.now, verbose_name='分析日期')
    target_segment = models.CharField(max_length=100, verbose_name='目标细分市场')
    analysis_data = models.JSONField(verbose_name='分析数据')  # 存储分析结果
    insights = models.TextField(verbose_name='分析洞察')
    
    class Meta:
        verbose_name = '市场分析'
        verbose_name_plural = verbose_name
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date}"
