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
    title = models.CharField(max_length=200, verbose_name='车辆名称')
    detail = models.TextField(verbose_name='车辆详情', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    detail_url = models.URLField(verbose_name='详情链接')
    registration_date = models.DateField(verbose_name='上牌时间', null=True, blank=True)
    mileage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='表显里程', null=True, blank=True)
    transmission = models.CharField(max_length=50, verbose_name='变速箱', blank=True, null=True)
    fuel_type = models.CharField(max_length=50, verbose_name='燃料类型', blank=True, null=True)
    nedc_range = models.IntegerField(verbose_name='NEDC纯电续航里程', null=True, blank=True)
    publish_date = models.DateTimeField(verbose_name='发布时间', null=True, blank=True)
    accident_check = models.CharField(max_length=100, verbose_name='出险查询', blank=True, null=True)
    inspection_due_date = models.DateField(verbose_name='年检到期', null=True, blank=True)
    insurance_due_date = models.DateField(verbose_name='保险到期', null=True, blank=True)
    maintenance = models.TextField(verbose_name='维修保养', blank=True, null=True)
    transfer_count = models.IntegerField(verbose_name='过户次数', null=True, blank=True)
    location = models.CharField(max_length=100, verbose_name='所在地')
    engine = models.CharField(max_length=100, verbose_name='发动机', blank=True, null=True)
    vehicle_class = models.CharField(max_length=50, verbose_name='车辆级别', blank=True, null=True)
    color = models.CharField(max_length=50, verbose_name='车身颜色', blank=True, null=True)
    drive_type = models.CharField(max_length=50, verbose_name='驱动方式', blank=True, null=True)
    standard_capacity = models.CharField(max_length=50, verbose_name='标准容量', blank=True, null=True)
    emission_standard = models.CharField(max_length=50, verbose_name='排放标准', blank=True, null=True)
    displacement = models.CharField(max_length=50, verbose_name='排量', blank=True, null=True)
    fuel_grade = models.CharField(max_length=50, verbose_name='燃油标号', blank=True, null=True)
    standard_slow_charging = models.CharField(max_length=100, verbose_name='标准慢充', blank=True, null=True)
    standard_fast_charging = models.CharField(max_length=100, verbose_name='标准快充', blank=True, null=True)
    cltc_range = models.IntegerField(verbose_name='CLTC纯电续航里程', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '二手车数据'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title