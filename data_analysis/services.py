import pandas as pd
import numpy as np
from django.db.models import Avg, Count, Sum, Min, Max, F, Q, FloatField
from django.db.models.functions import Cast
from crawler.models import Brand, CarModel, UsedCar
from .models import PriceAnalysisResult, BrandAnalysisResult, RegionAnalysisResult, VehicleAttributeAnalysisResult

class PriceAnalysisService:
    @staticmethod
    def analyze_brand_price():
        """分析各品牌的价格分布"""
        # 获取各品牌的价格统计数据
        brand_price_data = UsedCar.objects.values(
            'car_model__brand__name'
        ).annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            car_count=Count('id')
        ).filter(car_count__gte=5).order_by('-avg_price')  # 至少有5辆车的品牌
        
        # 转换为适合存储的格式
        result_data = {
            'brands': [item['car_model__brand__name'] for item in brand_price_data],
            'avg_prices': [float(item['avg_price']) for item in brand_price_data],
            'min_prices': [float(item['min_price']) for item in brand_price_data],
            'max_prices': [float(item['max_price']) for item in brand_price_data],
            'car_counts': [item['car_count'] for item in brand_price_data]
        }
        
        # 生成分析摘要
        top_brands = brand_price_data[:5]
        summary = f"价格最高的五个品牌是：{', '.join([item['car_model__brand__name'] for item in top_brands])}，"
        summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_brands])}"
        
        return result_data, summary
    
    @staticmethod
    def analyze_region_price():
        """分析各地区的价格水平"""
        # 获取各地区的价格统计数据
        region_price_data = UsedCar.objects.values(
            'location'
        ).annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            car_count=Count('id')
        ).filter(car_count__gte=3).order_by('-avg_price')  # 至少有3辆车的地区
        
        # 转换为适合存储的格式
        result_data = {
            'regions': [item['location'] for item in region_price_data],
            'avg_prices': [float(item['avg_price']) for item in region_price_data],
            'min_prices': [float(item['min_price']) for item in region_price_data],
            'max_prices': [float(item['max_price']) for item in region_price_data],
            'car_counts': [item['car_count'] for item in region_price_data]
        }
        
        # 生成分析摘要
        top_regions = region_price_data[:5]
        summary = f"价格水平最高的五个地区是：{', '.join([item['location'] for item in top_regions])}，"
        summary += f"平均价格分别为：{', '.join([str(round(float(item['avg_price']), 2)) + '万' for item in top_regions])}"
        
        return result_data, summary
    
    @staticmethod
    def analyze_year_price():
        """分析车辆年份与价格的关系"""
        # 获取各年份的价格统计数据
        year_price_data = UsedCar.objects.exclude(
            registration_date__isnull=True
        ).annotate(
            year=F('registration_date__year')
        ).values('year').annotate(
            avg_price=Avg('price'),
            car_count=Count('id')
        ).filter(car_count__gte=2).order_by('year')  # 至少有2辆车的年份
        
        # 转换为适合存储的格式
        result_data = {
            'years': [item['year'] for item in year_price_data],
            'avg_prices': [float(item['avg_price']) for item in year_price_data],
            'car_counts': [item['car_count'] for item in year_price_data]
        }
        
        # 生成分析摘要
        if year_price_data:
            newest_year = max(result_data['years'])
            oldest_year = min(result_data['years'])
            newest_price = next((p for y, p in zip(result_data['years'], result_data['avg_prices']) if y == newest_year), 0)
            oldest_price = next((p for y, p in zip(result_data['years'], result_data['avg_prices']) if y == oldest_year), 0)
            price_diff = newest_price - oldest_price
            avg_depreciation = price_diff / (newest_year - oldest_year) if newest_year != oldest_year else 0
            
            summary = f"{oldest_year}年至{newest_year}年的二手车平均价格变化为{round(price_diff, 2)}万元，"
            summary += f"平均每年折旧约{round(abs(avg_depreciation), 2)}万元。"
        else:
            summary = "暂无足够的数据进行年份价格分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_mileage_price():
        """分析里程数与价格的关系"""
        # 获取不同里程区间的价格统计数据
        cars_with_mileage = UsedCar.objects.exclude(mileage__isnull=True)
        
        # 定义里程区间
        mileage_ranges = [
            (0, 1),  # 0-1万公里
            (1, 3),  # 1-3万公里
            (3, 5),  # 3-5万公里
            (5, 8),  # 5-8万公里
            (8, 10), # 8-10万公里
            (10, 15), # 10-15万公里
            (15, float('inf'))  # 15万公里以上
        ]
        
        mileage_price_data = []
        for start, end in mileage_ranges:
            if end == float('inf'):
                range_cars = cars_with_mileage.filter(mileage__gte=start)
                range_label = f"{start}万公里以上"
            else:
                range_cars = cars_with_mileage.filter(mileage__gte=start, mileage__lt=end)
                range_label = f"{start}-{end}万公里"
            
            if range_cars.exists():
                avg_price = range_cars.aggregate(avg_price=Avg('price'))['avg_price']
                car_count = range_cars.count()
                mileage_price_data.append({
                    'range': range_label,
                    'avg_price': float(avg_price),
                    'car_count': car_count
                })
        
        # 转换为适合存储的格式
        result_data = {
            'ranges': [item['range'] for item in mileage_price_data],
            'avg_prices': [item['avg_price'] for item in mileage_price_data],
            'car_counts': [item['car_count'] for item in mileage_price_data]
        }
        
        # 生成分析摘要
        if mileage_price_data:
            lowest_price_range = min(mileage_price_data, key=lambda x: x['avg_price'])
            highest_price_range = max(mileage_price_data, key=lambda x: x['avg_price'])
            
            summary = f"里程在{highest_price_range['range']}的车辆平均价格最高，为{round(highest_price_range['avg_price'], 2)}万元；"
            summary += f"里程在{lowest_price_range['range']}的车辆平均价格最低，为{round(lowest_price_range['avg_price'], 2)}万元。"
        else:
            summary = "暂无足够的数据进行里程价格分析。"
        
        return result_data, summary

class BrandAnalysisService:
    @staticmethod
    def analyze_brand_popularity():
        """分析品牌流行度"""
        # 获取各品牌的车辆数量
        brand_popularity_data = Brand.objects.annotate(
            car_count=Count('car_models__used_cars')
        ).filter(car_count__gt=0).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'brands': [brand.name for brand in brand_popularity_data],
            'car_counts': [brand.car_count for brand in brand_popularity_data]
        }
        
        # 生成分析摘要
        top_brands = list(brand_popularity_data[:5])
        summary = f"最受欢迎的五个品牌是：{', '.join([brand.name for brand in top_brands])}，"
        summary += f"分别有{', '.join([str(brand.car_count) + '辆' for brand in top_brands])}二手车在售。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_brand_price_range():
        """分析品牌价格区间"""
        # 获取主要品牌的价格区间
        major_brands = Brand.objects.annotate(
            car_count=Count('car_models__used_cars')
        ).filter(car_count__gte=3)  # 至少有3辆车的品牌
        
        brand_price_range_data = []
        for brand in major_brands:
            brand_cars = UsedCar.objects.filter(car_model__brand=brand)
            price_stats = brand_cars.aggregate(
                min_price=Min('price'),
                max_price=Max('price'),
                avg_price=Avg('price'),
                car_count=Count('id')
            )
            
            brand_price_range_data.append({
                'brand': brand.name,
                'min_price': float(price_stats['min_price']),
                'max_price': float(price_stats['max_price']),
                'avg_price': float(price_stats['avg_price']),
                'price_range': float(price_stats['max_price'] - price_stats['min_price']),
                'car_count': price_stats['car_count']
            })
        
        # 按价格区间大小排序
        brand_price_range_data.sort(key=lambda x: x['price_range'], reverse=True)
        
        # 转换为适合存储的格式
        result_data = {
            'brands': [item['brand'] for item in brand_price_range_data],
            'min_prices': [item['min_price'] for item in brand_price_range_data],
            'max_prices': [item['max_price'] for item in brand_price_range_data],
            'avg_prices': [item['avg_price'] for item in brand_price_range_data],
            'price_ranges': [item['price_range'] for item in brand_price_range_data],
            'car_counts': [item['car_count'] for item in brand_price_range_data]
        }
        
        # 生成分析摘要
        if brand_price_range_data:
            widest_range_brand = brand_price_range_data[0]
            narrowest_range_brand = min(brand_price_range_data, key=lambda x: x['price_range'])
            
            summary = f"{widest_range_brand['brand']}的价格区间最大，从{round(widest_range_brand['min_price'], 2)}万元到{round(widest_range_brand['max_price'], 2)}万元，区间为{round(widest_range_brand['price_range'], 2)}万元；"
            summary += f"{narrowest_range_brand['brand']}的价格区间最小，从{round(narrowest_range_brand['min_price'], 2)}万元到{round(narrowest_range_brand['max_price'], 2)}万元，区间为{round(narrowest_range_brand['price_range'], 2)}万元。"
        else:
            summary = "暂无足够的数据进行品牌价格区间分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_brand_region_distribution():
        """分析品牌的地区分布"""
        # 获取主要品牌
        major_brands = Brand.objects.annotate(
            car_count=Count('car_models__used_cars')
        ).filter(car_count__gte=5).order_by('-car_count')[:10]  # 取前10个主要品牌
        
        brand_region_data = []
        for brand in major_brands:
            # 获取该品牌在各地区的车辆数量
            region_counts = UsedCar.objects.filter(
                car_model__brand=brand
            ).values('location').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # 取前3个主要地区
            main_regions = list(region_counts[:3])
            other_count = sum(item['count'] for item in region_counts[3:]) if len(region_counts) > 3 else 0
            
            brand_region_data.append({
                'brand': brand.name,
                'regions': [region['location'] for region in main_regions],
                'counts': [region['count'] for region in main_regions],
                'other_count': other_count,
                'total_count': sum(region['count'] for region in region_counts)
            })
        
        # 转换为适合存储的格式
        result_data = {
            'brands': [item['brand'] for item in brand_region_data],
            'region_data': [{
                'regions': item['regions'],
                'counts': item['counts'],
                'other_count': item['other_count'],
                'total_count': item['total_count']
            } for item in brand_region_data]
        }
        
        # 生成分析摘要
        if brand_region_data:
            top_brand = brand_region_data[0]
            top_regions = ', '.join([f"{region}({count}辆)" for region, count in zip(top_brand['regions'], top_brand['counts'])])
            
            summary = f"{top_brand['brand']}品牌二手车主要分布在以下地区：{top_regions}，"
            summary += f"其他地区共有{top_brand['other_count']}辆。"
        else:
            summary = "暂无足够的数据进行品牌地区分布分析。"
        
        return result_data, summary

class RegionAnalysisService:
    @staticmethod
    def analyze_region_car_count():
        """分析各地区的车辆数量"""
        # 获取各地区的车辆数量
        region_car_count_data = UsedCar.objects.values('location').annotate(
            car_count=Count('id')
        ).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'regions': [item['location'] for item in region_car_count_data],
            'car_counts': [item['car_count'] for item in region_car_count_data]
        }
        
        # 生成分析摘要
        top_regions = list(region_car_count_data[:5])
        summary = f"二手车数量最多的五个地区是：{', '.join([region['location'] for region in top_regions])}，"
        summary += f"分别有{', '.join([str(region['car_count']) + '辆' for region in top_regions])}二手车在售。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_region_price_level():
        """分析各地区的价格水平"""
        # 获取各地区的价格水平
        region_price_level_data = UsedCar.objects.values('location').annotate(
            avg_price=Avg('price'),
            car_count=Count('id')
        ).filter(car_count__gte=3).order_by('-avg_price')  # 至少有3辆车的地区
        
        # 转换为适合存储的格式
        result_data = {
            'regions': [item['location'] for item in region_price_level_data],
            'avg_prices': [float(item['avg_price']) for item in region_price_level_data],
            'car_counts': [item['car_count'] for item in region_price_level_data]
        }
        
        # 生成分析摘要
        if region_price_level_data:
            highest_price_region = region_price_level_data[0]
            lowest_price_region = region_price_level_data.last()
            
            summary = f"二手车均价最高的地区是{highest_price_region['location']}，平均价格为{round(float(highest_price_region['avg_price']), 2)}万元；"
            summary += f"均价最低的地区是{lowest_price_region['location']}，平均价格为{round(float(lowest_price_region['avg_price']), 2)}万元。"
        else:
            summary = "暂无足够的数据进行地区价格水平分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_region_brand_preference():
        """分析各地区的品牌偏好"""
        # 获取主要地区
        major_regions = UsedCar.objects.values('location').annotate(
            car_count=Count('id')
        ).filter(car_count__gte=5).order_by('-car_count')[:10]  # 取前10个主要地区
        
        region_brand_data = []
        for region_data in major_regions:
            region = region_data['location']
            # 获取该地区各品牌的车辆数量
            brand_counts = UsedCar.objects.filter(
                location=region
            ).values('car_model__brand__name').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # 取前3个主要品牌
            main_brands = list(brand_counts[:3])
            other_count = sum(item['count'] for item in brand_counts[3:]) if len(brand_counts) > 3 else 0
            
            region_brand_data.append({
                'region': region,
                'brands': [brand['car_model__brand__name'] for brand in main_brands],
                'counts': [brand['count'] for brand in main_brands],
                'other_count': other_count,
                'total_count': region_data['car_count']
            })
        
        # 转换为适合存储的格式
        result_data = {
            'regions': [item['region'] for item in region_brand_data],
            'brand_data': [{
                'brands': item['brands'],
                'counts': item['counts'],
                'other_count': item['other_count'],
                'total_count': item['total_count']
            } for item in region_brand_data]
        }
        
        # 生成分析摘要
        if region_brand_data:
            top_region = region_brand_data[0]
            top_brands = ', '.join([f"{brand}({count}辆)" for brand, count in zip(top_region['brands'], top_region['counts'])])
            
            summary = f"{top_region['region']}地区最受欢迎的品牌是：{top_brands}，"
            summary += f"其他品牌共有{top_region['other_count']}辆。"
        else:
            summary = "暂无足够的数据进行地区品牌偏好分析。"
        
        return result_data, summary

class VehicleAttributeAnalysisService:
    @staticmethod
    def analyze_fuel_type():
        """分析燃料类型分布"""
        # 获取各燃料类型的车辆数量
        fuel_type_data = UsedCar.objects.exclude(
            fuel_type__isnull=True
        ).exclude(
            fuel_type=''
        ).values('fuel_type').annotate(
            car_count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'fuel_types': [item['fuel_type'] for item in fuel_type_data],
            'car_counts': [item['car_count'] for item in fuel_type_data],
            'avg_prices': [float(item['avg_price']) for item in fuel_type_data]
        }
        
        # 生成分析摘要
        if fuel_type_data:
            top_fuel_types = list(fuel_type_data[:3])
            summary = f"最常见的三种燃料类型是：{', '.join([item['fuel_type'] for item in top_fuel_types])}，"
            summary += f"分别占比{', '.join([str(round(item['car_count'] / sum(result_data['car_counts']) * 100, 1)) + '%' for item in top_fuel_types])}。"
        else:
            summary = "暂无足够的数据进行燃料类型分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_transmission():
        """分析变速箱类型分布"""
        # 获取各变速箱类型的车辆数量
        transmission_data = UsedCar.objects.exclude(
            transmission__isnull=True
        ).exclude(
            transmission=''
        ).values('transmission').annotate(
            car_count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'transmission_types': [item['transmission'] for item in transmission_data],
            'car_counts': [item['car_count'] for item in transmission_data],
            'avg_prices': [float(item['avg_price']) for item in transmission_data]
        }
        
        # 生成分析摘要
        if transmission_data:
            top_transmission_types = list(transmission_data[:3])
            summary = f"最常见的三种变速箱类型是：{', '.join([item['transmission'] for item in top_transmission_types])}，"
            summary += f"分别占比{', '.join([str(round(item['car_count'] / sum(result_data['car_counts']) * 100, 1)) + '%' for item in top_transmission_types])}。"
        else:
            summary = "暂无足够的数据进行变速箱类型分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_color_preference():
        """分析车身颜色偏好"""
        # 获取各车身颜色的车辆数量
        color_data = UsedCar.objects.exclude(
            color__isnull=True
        ).exclude(
            color=''
        ).values('color').annotate(
            car_count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'colors': [item['color'] for item in color_data],
            'car_counts': [item['car_count'] for item in color_data],
            'avg_prices': [float(item['avg_price']) for item in color_data]
        }
        
        # 生成分析摘要
        if color_data:
            top_colors = list(color_data[:3])
            summary = f"最受欢迎的三种车身颜色是：{', '.join([item['color'] for item in top_colors])}，"
            summary += f"分别占比{', '.join([str(round(item['car_count'] / sum(result_data['car_counts']) * 100, 1)) + '%' for item in top_colors])}。"
        else:
            summary = "暂无足够的数据进行车身颜色偏好分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_engine_type():
        """分析发动机类型分布"""
        # 获取各发动机类型的车辆数量
        engine_data = UsedCar.objects.exclude(
            engine__isnull=True
        ).exclude(
            engine=''
        ).values('engine').annotate(
            car_count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-car_count')
        
        # 转换为适合存储的格式
        result_data = {
            'engine_types': [item['engine'] for item in engine_data],
            'car_counts': [item['car_count'] for item in engine_data],
            'avg_prices': [float(item['avg_price']) for item in engine_data]
        }
        
        # 生成分析摘要
        if engine_data:
            top_engine_types = list(engine_data[:3])
            summary = f"最常见的三种发动机类型是：{', '.join([item['engine'] for item in top_engine_types])}，"
            summary += f"分别占比{', '.join([str(round(item['car_count'] / sum(result_data['car_counts']) * 100, 1)) + '%' for item in top_engine_types])}。"
        else:
            summary = "暂无足够的数据进行发动机类型分析。"
        
        return result_data, summary
    
    @staticmethod
    def analyze_mileage_distribution():
        """分析里程分布"""
        # 获取里程数据
        cars_with_mileage = UsedCar.objects.exclude(mileage__isnull=True)
        
        # 定义里程区间
        mileage_ranges = [
            (0, 1),  # 0-1万公里
            (1, 3),  # 1-3万公里
            (3, 5),  # 3-5万公里
            (5, 8),  # 5-8万公里
            (8, 10), # 8-10万公里
            (10, 15), # 10-15万公里
            (15, float('inf'))  # 15万公里以上
        ]
        
        mileage_distribution_data = []
        for start, end in mileage_ranges:
            if end == float('inf'):
                range_cars = cars_with_mileage.filter(mileage__gte=start)
                range_label = f"{start}万公里以上"
            else:
                range_cars = cars_with_mileage.filter(mileage__gte=start, mileage__lt=end)
                range_label = f"{start}-{end}万公里"
            
            if range_cars.exists():
                car_count = range_cars.count()
                avg_price = range_cars.aggregate(avg_price=Avg('price'))['avg_price']
                mileage_distribution_data.append({
                    'range': range_label,
                    'car_count': car_count,
                    'avg_price': float(avg_price)
                })
        
        # 转换为适合存储的格式
        result_data = {
            'ranges': [item['range'] for item in mileage_distribution_data],
            'car_counts': [item['car_count'] for item in mileage_distribution_data],
            'avg_prices': [item['avg_price'] for item in mileage_distribution_data]
        }
        
        # 生成分析摘要
        if mileage_distribution_data:
            most_common_range = max(mileage_distribution_data, key=lambda x: x['car_count'])
            total_cars = sum(item['car_count'] for item in mileage_distribution_data)
            
            summary = f"最常见的里程区间是{most_common_range['range']}，有{most_common_range['car_count']}辆车，"
            summary += f"占比{round(most_common_range['car_count'] / total_cars * 100, 1)}%。"
        else:
            summary = "暂无足够的数据进行里程分布分析。"
        
        return result_data, summary