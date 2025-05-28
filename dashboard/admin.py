from django.contrib import admin
from .models import Brand, CarModel, PriceHistory, SalesData, UserRating

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'body_type', 'price_range', 'launch_date', 'is_listed')
    list_filter = ('brand', 'body_type', 'is_listed')
    search_fields = ('name', 'brand__name')
    date_hierarchy = 'launch_date'

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('car', 'price', 'date')
    list_filter = ('car__brand', 'date')
    search_fields = ('car__name', 'car__brand__name')
    date_hierarchy = 'date'

@admin.register(SalesData)
class SalesDataAdmin(admin.ModelAdmin):
    list_display = ('car', 'month', 'sales_volume')
    list_filter = ('car__brand', 'month')
    search_fields = ('car__name', 'car__brand__name')
    date_hierarchy = 'month'

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('car', 'overall_rating', 'created_at')
    list_filter = ('car__brand', 'created_at')
    search_fields = ('car__name', 'car__brand__name', 'comment')
    date_hierarchy = 'created_at'
