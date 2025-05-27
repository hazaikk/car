# scripts/import_data.py
import os
import django
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardata_platform.settings')
django.setup()

import pandas as pd
from crawler.models import Brand, CarModel, UsedCar

def import_data():
    # 读取Excel文件
    df = pd.read_excel('二手车数据.xlsx')
    
    # 处理数据并导入到数据库
    for _, row in df.iterrows():
        # 提取品牌和车型
        car_name = row.get('车辆名称', '')
        if not car_name:
            continue
            
        # 简单处理，假设第一个词是品牌
        parts = car_name.split()
        brand_name = parts[0] if parts else '未知品牌'
        model_name = ' '.join(parts[1:]) if len(parts) > 1 else '未知车型'
        
        # 获取或创建品牌
        brand, _ = Brand.objects.get_or_create(name=brand_name)
        
        # 获取或创建车型
        car_model, _ = CarModel.objects.get_or_create(
            brand=brand,
            name=model_name
        )
        
        # 创建二手车数据
        price_str = str(row.get('价格', '0')).replace('万', '').strip()
        if price_str.lower() == 'nan' or price_str == '':
            price = 0
        else:
            try:
                price = float(price_str)
            except ValueError:
                price = 0
            
        # 提取其他信息
        detail_url = row.get('详情链接', '')
        
        # 处理上牌时间字段
        reg_time = row.get('上牌时间', '')
        reg_time_str = str(reg_time)
        if '-' in reg_time_str:
            year = reg_time_str.split('-')[0]
        elif reg_time_str.lower() == 'nan' or reg_time_str == '':
            year = 2020
        else:
            try:
                year = int(float(reg_time_str))
            except Exception:
                year = 2020
        # 创建二手车记录
        mileage_str = str(row.get('表显里程', '0')).replace('万公里', '').strip()
        try:
            mileage = float(mileage_str) if mileage_str.lower() != 'nan' and mileage_str != '' else 0
        except Exception:
            mileage = 0
            UsedCar.objects.create(
                car_model=car_model,
                title=car_name,
                price=price,
                year=year,
                mileage=mileage,
                location=row.get('车辆所在地', ''),
                color=row.get('车身颜色', ''),
                displacement=row.get('排量', ''),
                transmission=row.get('变速箱', ''),
                fuel_type=row.get('燃油类型', ''),
                detail_url=detail_url
            )
    
    print(f"导入完成，共导入{UsedCar.objects.count()}条数据")

if __name__ == '__main__':
    import_data()