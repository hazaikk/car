import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime, timedelta
from dashboard.models import SalesData, PriceHistory
from .models import SalesAnalysis, PriceAnalysis, MarketAnalysis

class SalesAnalysisService:
    @staticmethod
    def prepare_sales_data(car_id, months=24):
        """准备销量数据"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months*30)
        
        sales_data = SalesData.objects.filter(
            car_id=car_id,
            month__gte=start_date,
            month__lte=end_date
        ).order_by('month')
        
        if not sales_data:
            return None, None
            
        dates = [sale.month for sale in sales_data]
        volumes = [sale.sales_volume for sale in sales_data]
        
        # 将日期转换为数值特征（距离起始日期的月数）
        X = np.array([(date - dates[0]).days / 30 for date in dates]).reshape(-1, 1)
        y = np.array(volumes)
        
        return X, y
    
    @staticmethod
    def predict_sales(car_id, forecast_months=6):
        """预测未来销量"""
        X, y = SalesAnalysisService.prepare_sales_data(car_id)
        if X is None or len(X) < 12:  # 至少需要12个月的数据
            return None
            
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 训练模型
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test)
        accuracy = r2_score(y_test, y_pred)
        
        # 预测未来销量
        last_month = X[-1][0]
        future_months = np.array(range(int(last_month) + 1, int(last_month) + forecast_months + 1)).reshape(-1, 1)
        future_predictions = model.predict(future_months)
        
        # 准备预测数据
        prediction_data = {
            'months': [int(m[0]) for m in future_months],
            'predictions': [int(p) for p in future_predictions]
        }
        
        return prediction_data, accuracy

class PriceAnalysisService:
    @staticmethod
    def prepare_price_data(car_id, days=365):
        """准备价格数据"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        price_data = PriceHistory.objects.filter(
            car_id=car_id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        if not price_data:
            return None, None
            
        dates = [price.date for price in price_data]
        prices = [float(price.price) for price in price_data]
        
        # 将日期转换为数值特征（距离起始日期的天数）
        X = np.array([(date - dates[0]).days for date in dates]).reshape(-1, 1)
        y = np.array(prices)
        
        return X, y
    
    @staticmethod
    def analyze_price_trend(car_id, forecast_days=30):
        """分析价格趋势并预测"""
        X, y = PriceAnalysisService.prepare_price_data(car_id)
        if X is None or len(X) < 30:  # 至少需要30天的数据
            return None
            
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 训练模型
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 计算趋势
        trend_coefficient = model.coef_[0]  # 价格变化率（元/天）
        trend_type = '上涨' if trend_coefficient > 0 else '下跌' if trend_coefficient < 0 else '稳定'
        
        # 评估模型
        y_pred = model.predict(X_test)
        confidence = r2_score(y_test, y_pred)
        
        # 预测未来价格
        last_day = X[-1][0]
        future_days = np.array(range(int(last_day) + 1, int(last_day) + forecast_days + 1)).reshape(-1, 1)
        future_predictions = model.predict(future_days)
        
        # 准备分析数据
        trend_data = {
            'trend_type': trend_type,
            'change_rate': float(trend_coefficient),
            'avg_price': float(y.mean()),
            'min_price': float(y.min()),
            'max_price': float(y.max())
        }
        
        prediction_data = {
            'days': [int(d[0]) for d in future_days],
            'predictions': [float(p) for p in future_predictions]
        }
        
        return trend_data, prediction_data, confidence

class MarketAnalysisService:
    @staticmethod
    def analyze_market_segment(segment, date_range=None):
        """分析细分市场"""
        if date_range is None:
            date_range = {
                'start': datetime.now().date() - timedelta(days=365),
                'end': datetime.now().date()
            }
        
        # 获取该细分市场的所有车型
        cars = CarModel.objects.filter(body_type=segment)
        
        # 分析销量
        sales_data = SalesData.objects.filter(
            car__in=cars,
            month__gte=date_range['start'],
            month__lte=date_range['end']
        ).values('car__brand__name').annotate(
            total_sales=Sum('sales_volume'),
            avg_sales=Avg('sales_volume')
        ).order_by('-total_sales')
        
        # 分析价格
        price_data = PriceHistory.objects.filter(
            car__in=cars,
            date__gte=date_range['start'],
            date__lte=date_range['end']
        ).values('car__brand__name').annotate(
            avg_price=Avg('price'),
            price_range=Max('price') - Min('price')
        )
        
        # 准备分析结果
        analysis_data = {
            'segment_overview': {
                'total_models': cars.count(),
                'avg_price': float(price_data.aggregate(Avg('avg_price'))['avg_price__avg'] or 0),
                'total_sales': int(sales_data.aggregate(Sum('total_sales'))['total_sales__sum'] or 0)
            },
            'brand_performance': [
                {
                    'brand': item['car__brand__name'],
                    'total_sales': int(item['total_sales']),
                    'avg_sales': float(item['avg_sales']),
                    'market_share': float(item['total_sales'] / sales_data.aggregate(Sum('total_sales'))['total_sales__sum'] * 100)
                }
                for item in sales_data
            ],
            'price_analysis': [
                {
                    'brand': item['car__brand__name'],
                    'avg_price': float(item['avg_price']),
                    'price_range': float(item['price_range'])
                }
                for item in price_data
            ]
        }
        
        return analysis_data 