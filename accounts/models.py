from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """用户资料"""
    USER_TYPE_CHOICES = (
        ('normal', '普通用户'),
        ('enterprise', '企业用户'),
        ('admin', '管理员'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='normal', verbose_name='用户类型')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='电话')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='公司名称')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.user.username

class UserPreference(models.Model):
    """用户偏好"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    favorite_brands = models.ManyToManyField('crawler.Brand', blank=True, related_name='favorited_by', verbose_name='喜欢的品牌')
    price_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='最低价格')
    price_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='最高价格')
    year_min = models.IntegerField(blank=True, null=True, verbose_name='最早年份')
    
    class Meta:
        verbose_name = '用户偏好'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.user.username}的偏好"