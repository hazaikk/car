from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Brand(models.Model):
    """汽车品牌模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='品牌名称')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '品牌'
        verbose_name_plural = '品牌'
        ordering = ['name']
        
    def __str__(self):
        return self.name

class CarModel(models.Model):
    """车型模型"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='品牌')
    name = models.CharField(max_length=200, verbose_name='车型名称')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '车型'
        verbose_name_plural = '车型'
        unique_together = ['brand', 'name']
        ordering = ['brand__name', 'name']
        
    def __str__(self):
        return f"{self.brand.name} {self.name}"

class UsedCar(models.Model):
    """二手车数据模型"""
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, null=True, blank=True, verbose_name='车型')
    title = models.CharField(max_length=500, verbose_name='车辆标题')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='价格(万元)')
    mileage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='里程(万公里)', default=None)
    mileage_text = models.CharField(max_length=50, null=True, blank=True, verbose_name='里程原始文本', default='')
    location = models.CharField(max_length=100, null=True, blank=True, verbose_name='所在地')
    detail_url = models.URLField(max_length=1000, null=True, blank=True, verbose_name='详情链接')
    
    # 车辆详细信息
    accident_check = models.CharField(max_length=100, null=True, blank=True, verbose_name='事故排查')
    first_registration = models.CharField(max_length=100, null=True, blank=True, verbose_name='首次上牌')
    registration_date = models.DateField(null=True, blank=True, verbose_name='上牌日期', default=None)
    annual_inspection = models.CharField(max_length=100, null=True, blank=True, verbose_name='年检到期')
    insurance_expiry = models.CharField(max_length=100, null=True, blank=True, verbose_name='保险到期')
    transfer_count = models.CharField(max_length=100, null=True, blank=True, verbose_name='过户次数')
    usage_nature = models.CharField(max_length=100, null=True, blank=True, verbose_name='使用性质')
    displacement = models.CharField(max_length=100, null=True, blank=True, verbose_name='排量')
    gearbox = models.CharField(max_length=100, null=True, blank=True, verbose_name='变速箱')
    fuel_type = models.CharField(max_length=100, null=True, blank=True, verbose_name='燃料类型')
    drive_type = models.CharField(max_length=100, null=True, blank=True, verbose_name='驱动方式')
    emission_standard = models.CharField(max_length=100, null=True, blank=True, verbose_name='排放标准')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '二手车'
        verbose_name_plural = '二手车'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title

class CrawlerTask(models.Model):
    """爬虫任务模型"""
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('stopped', '已停止'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='任务名称')
    target_count = models.IntegerField(default=100, verbose_name='目标爬取数量')
    actual_count = models.IntegerField(default=0, verbose_name='实际爬取数量')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    # 爬虫参数
    start_page = models.IntegerField(default=1, verbose_name='起始页码')
    end_page = models.IntegerField(null=True, blank=True, verbose_name='终止页码')
    delay_seconds = models.FloatField(default=2.0, verbose_name='爬取间隔(秒)')
    search_keyword = models.CharField(max_length=100, null=True, blank=True, verbose_name='搜索关键词')
    
    # 爬取的数据存储
    crawled_data = models.JSONField(default=list, verbose_name='爬取的数据')
    
    class Meta:
        verbose_name = '爬虫任务'
        verbose_name_plural = '爬虫任务'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def progress_percentage(self):
        """计算进度百分比"""
        if self.target_count == 0:
            return 0
        return min(100, (self.actual_count / self.target_count) * 100)