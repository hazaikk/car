from django.db import models
from django.contrib.auth.models import User

def analysis_image_path(instance, filename):
    """生成分析图片的上传路径"""
    return f'analysis_results/{instance.analysis_type}/{filename}'

def analysis_data_path(instance, filename):
    """生成分析数据文件的上传路径"""
    return f'analysis_data/{instance.analysis_type}/{filename}'

class AnalysisResult(models.Model):
    """分析结果模型"""
    ANALYSIS_TYPE_CHOICES = [
        ('price_by_brand', '品牌价格分析'),
        ('price_by_region', '地区价格分析'),
        ('price_by_year', '年份价格分析'),
        ('price_by_mileage', '里程价格分析'),
        ('count_by_brand', '品牌数量分析'),
        ('count_by_region', '地区数量分析'),
        ('count_by_fuel', '燃料类型分析'),
        ('count_by_transmission', '变速箱类型分析'),
        ('count_by_color', '车身颜色分析'),
    ]
    
    title = models.CharField(max_length=100, verbose_name='标题')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES, verbose_name='分析类型')
    image = models.ImageField(upload_to=analysis_image_path, verbose_name='分析图片')
    data_file = models.FileField(upload_to=analysis_data_path, blank=True, null=True, verbose_name='数据文件')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分析结果'
        verbose_name_plural = '分析结果'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
