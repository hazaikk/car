from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AnalysisRecord(models.Model):
    """保存用户进行的分析记录"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='分析用户')
    analysis_type = models.CharField(max_length=100, verbose_name='分析类型')
    parameters = models.JSONField(verbose_name='分析参数', default=dict, blank=True)
    # 结果摘要可以存储图表的主要数据点，或者一个简短的文字描述
    result_summary = models.TextField(verbose_name='结果摘要', blank=True, null=True) 
    # 如果需要存储图表图片，可以添加 ImageField，但这里为了简化，只存摘要
    # chart_image = models.ImageField(upload_to='analysis_charts/', blank=True, null=True, verbose_name='分析图表')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '分析记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analysis_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"