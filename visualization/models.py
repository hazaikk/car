from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Chart(models.Model):
    """图表配置"""
    CHART_TYPES = (
        ('line', '折线图'),
        ('bar', '柱状图'),
        ('pie', '饼图'),
        ('scatter', '散点图'),
        ('heatmap', '热力图'),
        ('radar', '雷达图'),
    )
    
    DATA_TYPES = (
        ('sales', '销量数据'),
        ('price', '价格数据'),
        ('rating', '评分数据'),
        ('comment', '评论数据'),
    )

    title = models.CharField(max_length=100, verbose_name='图表标题')
    description = models.TextField(blank=True, null=True, verbose_name='图表描述')
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, verbose_name='图表类型')
    data_type = models.CharField(max_length=20, choices=DATA_TYPES, verbose_name='数据类型')
    config = models.JSONField(default=dict, verbose_name='图表配置')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    
    class Meta:
        verbose_name = '图表'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Dashboard(models.Model):
    """仪表盘"""
    title = models.CharField(max_length=100, verbose_name='仪表盘标题')
    description = models.TextField(blank=True, null=True, verbose_name='仪表盘描述')
    charts = models.ManyToManyField(Chart, through='DashboardChart', verbose_name='包含的图表')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    
    class Meta:
        verbose_name = '仪表盘'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class DashboardChart(models.Model):
    """仪表盘中的图表布局"""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, verbose_name='所属仪表盘')
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, verbose_name='图表')
    position_x = models.IntegerField(default=0, verbose_name='X轴位置')
    position_y = models.IntegerField(default=0, verbose_name='Y轴位置')
    width = models.IntegerField(default=6, verbose_name='宽度')
    height = models.IntegerField(default=4, verbose_name='高度')
    
    class Meta:
        verbose_name = '仪表盘图表'
        verbose_name_plural = verbose_name
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return f"{self.dashboard.title} - {self.chart.title}"

class ChartFilter(models.Model):
    """图表筛选条件"""
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='filters', verbose_name='所属图表')
    field_name = models.CharField(max_length=50, verbose_name='字段名')
    operator = models.CharField(max_length=20, verbose_name='操作符')
    value = models.CharField(max_length=200, verbose_name='筛选值')
    
    class Meta:
        verbose_name = '图表筛选'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.chart.title} - {self.field_name} {self.operator} {self.value}"
