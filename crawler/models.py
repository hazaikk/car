from django.db import models

class Brand(models.Model):
    """汽车品牌"""
    name = models.CharField(max_length=100, verbose_name='品牌名称')
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name='品牌logo')
    
    class Meta:
        verbose_name = '汽车品牌'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name

class CarModel(models.Model):
    """汽车车型"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='car_models', verbose_name='所属品牌')
    name = models.CharField(max_length=100, verbose_name='车型名称')
    
    class Meta:
        verbose_name = '汽车车型'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"

class UsedCar(models.Model):
    """二手车数据"""
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name='used_cars', verbose_name='车型')
    title = models.CharField(max_length=200, verbose_name='标题')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格(万)')
    year = models.IntegerField(verbose_name='年份')
    mileage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='里程(万公里)')
    location = models.CharField(max_length=100, verbose_name='地区')
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name='颜色')
    displacement = models.CharField(max_length=50, blank=True, null=True, verbose_name='排量')
    transmission = models.CharField(max_length=50, blank=True, null=True, verbose_name='变速箱')
    fuel_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='燃油类型')
    detail_url = models.URLField(verbose_name='详情链接')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '二手车数据'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title