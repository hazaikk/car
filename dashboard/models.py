from django.db import models
from django.utils import timezone

class Brand(models.Model):
    """汽车品牌"""
    name = models.CharField(max_length=100, unique=True, verbose_name='品牌名称')
    logo = models.ImageField(upload_to='brands/logos/', blank=True, null=True, verbose_name='品牌标志')
    description = models.TextField(blank=True, null=True, verbose_name='品牌描述')
    
    class Meta:
        verbose_name = '品牌'
        verbose_name_plural = verbose_name
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CarModel(models.Model):
    """车型"""
    BODY_TYPES = (
        ('sedan', '轿车'),
        ('suv', 'SUV'),
        ('mpv', 'MPV'),
        ('sports', '跑车'),
        ('pickup', '皮卡'),
    )
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='品牌')
    name = models.CharField(max_length=200, verbose_name='车型名称')
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, verbose_name='车身类型')
    price_range = models.CharField(max_length=100, verbose_name='价格区间')
    launch_date = models.DateField(verbose_name='上市日期')
    is_listed = models.BooleanField(default=True, verbose_name='是否在售')
    
    # 基本参数
    length = models.IntegerField(verbose_name='长度(mm)')
    width = models.IntegerField(verbose_name='宽度(mm)')
    height = models.IntegerField(verbose_name='高度(mm)')
    wheelbase = models.IntegerField(verbose_name='轴距(mm)')
    engine = models.CharField(max_length=100, verbose_name='发动机')
    transmission = models.CharField(max_length=100, verbose_name='变速箱')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '车型'
        verbose_name_plural = verbose_name
        ordering = ['brand', 'name']
        unique_together = ['brand', 'name']
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"

class PriceHistory(models.Model):
    """价格历史"""
    car = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name='车型')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    date = models.DateField(verbose_name='日期')
    
    class Meta:
        verbose_name = '价格历史'
        verbose_name_plural = verbose_name
        ordering = ['-date']
        unique_together = ['car', 'date']
    
    def __str__(self):
        return f"{self.car} - {self.date} - {self.price}万"

class SalesData(models.Model):
    """销量数据"""
    car = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name='车型')
    month = models.DateField(verbose_name='月份')
    sales_volume = models.IntegerField(verbose_name='销量')
    
    class Meta:
        verbose_name = '销量数据'
        verbose_name_plural = verbose_name
        ordering = ['-month']
        unique_together = ['car', 'month']
    
    def __str__(self):
        return f"{self.car} - {self.month.strftime('%Y-%m')} - {self.sales_volume}辆"

class UserRating(models.Model):
    """用户评分"""
    car = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name='车型')
    overall_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='综合评分')
    exterior_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='外观评分')
    interior_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='内饰评分')
    configuration_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='配置评分')
    performance_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='性能评分')
    comfort_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='舒适度评分')
    cost_performance_rating = models.DecimalField(max_digits=2, decimal_places=1, verbose_name='性价比评分')
    comment = models.TextField(blank=True, null=True, verbose_name='评价内容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='评价时间')
    
    class Meta:
        verbose_name = '用户评分'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.car} - {self.overall_rating}分"
