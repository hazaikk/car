from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    """用户资料"""
    EDUCATION_CHOICES = (
        ('high_school', '高中及以下'),
        ('college', '大专'),
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('phd', '博士'),
    )
    
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name='个人简介')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name='性别')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='电话')
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name='地址')
    education = models.CharField(max_length=20, choices=EDUCATION_CHOICES, blank=True, null=True, verbose_name='学历')
    occupation = models.CharField(max_length=100, blank=True, null=True, verbose_name='职业')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='公司')
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='个人网站')
    social_github = models.URLField(max_length=200, blank=True, null=True, verbose_name='GitHub')
    social_weibo = models.URLField(max_length=200, blank=True, null=True, verbose_name='微博')
    social_wechat = models.CharField(max_length=100, blank=True, null=True, verbose_name='微信')
    interests = models.TextField(max_length=500, blank=True, null=True, verbose_name='兴趣爱好')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username}的资料"

    def get_avatar_url(self):
        if self.avatar and self.avatar.url:
            return self.avatar.url
        return '/static/images/default-avatar.svg'

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