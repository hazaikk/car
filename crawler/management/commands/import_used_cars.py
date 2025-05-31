import pandas as pd
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from crawler.models import Brand, CarModel, UsedCar
from decimal import Decimal, InvalidOperation
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Import used car data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def clean_brand_model(self, title):
        """从车辆名称中提取品牌和车型"""
        parts = title.split(' ', 1)
        if len(parts) < 2:
            return '未知品牌', title
        return parts[0], parts[1]

    def parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str or pd.isna(date_str) or date_str == '-':
            return None
            
        try:
            # 处理"2019年03月"格式
            if '年' in date_str and '月' in date_str:
                year = int(date_str.split('年')[0])
                month = int(date_str.split('年')[1].split('月')[0])
                return datetime(year, month, 1).date()
            
            # 处理"2026-03"格式
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 2:
                    return datetime(int(parts[0]), int(parts[1]), 1).date()
                else:
                    return parse_date(date_str)
                    
            # 处理"2027-1"格式
            elif '-' in date_str:
                year, month = date_str.split('-')
                return datetime(int(year), int(month), 1).date()
        except:
            return None

    def parse_mileage(self, mileage_str):
        """解析里程数，返回万公里为单位的数值"""
        if not mileage_str or pd.isna(mileage_str):
            return None
            
        try:
            # 处理"6.7万公里"格式，直接提取数值（已经是万公里单位）
            if '万公里' in str(mileage_str):
                value = float(str(mileage_str).replace('万公里', ''))
                return Decimal(str(value))
            # 处理纯数字格式，假设是公里，转换为万公里
            elif str(mileage_str).replace('.', '').isdigit():
                value = float(str(mileage_str)) / 10000
                return Decimal(str(value))
            return None
        except:
            return None

    def parse_price(self, price):
        """解析价格"""
        if pd.isna(price):
            return Decimal('0.00')
        try:
            return Decimal(str(price))
        except:
            return Decimal('0.00')

    def parse_transfer_count(self, transfer_str):
        """解析过户次数"""
        if not transfer_str or pd.isna(transfer_str):
            return None
        try:
            # 提取数字
            num = ''.join(filter(str.isdigit, str(transfer_str)))
            return int(num) if num else None
        except:
            return None

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        if not os.path.exists(excel_file):
            self.stdout.write(self.style.ERROR(f'File not found: {excel_file}'))
            return

        # 清空现有数据
        UsedCar.objects.all().delete()
        CarModel.objects.all().delete()
        Brand.objects.all().delete()

        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file)

            # 打印所有列名，用于调试
            self.stdout.write("\nAvailable columns in Excel:")
            for col in df.columns:
                self.stdout.write(f"'{col}'")

            # 基本字段映射
            field_mapping = {
                '车辆名称': 'title',
                '车辆详情': 'detail',
                '价格': 'price',
                '详情链接': 'detail_url',
                '上牌时间': 'registration_date',
                '表显里程': 'mileage',
                '燃料类型': 'fuel_type',
                'NEDC纯电续航里程': 'nedc_range',
                '发布时间': 'publish_date',
                '出险查询': 'accident_check',
                '年检到期': 'inspection_due_date',
                '保险到期': 'insurance_due_date',
                '维修保养': 'maintenance',
                '过户次数': 'transfer_count',
                '车辆级别': 'vehicle_class',
                '车身颜色': 'color',
                '驱动方式': 'drive_type',
                '标准容量': 'standard_capacity',
                '排放标准': 'emission_standard',
                '燃油标号': 'fuel_grade',
                '标准慢充': 'standard_slow_charging',
                '标准快充': 'standard_fast_charging',
                'CLTC纯电续航里程': 'cltc_range'
            }

            success_count = 0
            error_count = 0

            # 打印第一行数据用于调试
            first_row = df.iloc[0]
            self.stdout.write("\nFirst row data:")
            for col in df.columns:
                self.stdout.write(f"{col}: {first_row[col]}")

            for idx, row in df.iterrows():
                try:
                    car_data = {}

                    # 处理基本字段
                    for excel_col, model_field in field_mapping.items():
                        if excel_col in df.columns:
                            value = row[excel_col]
                            
                            # 跳过空值和'-'
                            if pd.isna(value) or value == '-' or str(value).strip() == '':
                                continue

                            # 根据字段类型处理数据
                            if model_field == 'price':
                                car_data[model_field] = self.parse_price(value)
                            
                            elif model_field == 'mileage':
                                parsed_mileage = self.parse_mileage(value)
                                if parsed_mileage is not None:
                                    car_data[model_field] = parsed_mileage
                                    car_data['mileage_text'] = str(value)  # 保存原始文本
                            
                            elif model_field in ['registration_date', 'inspection_due_date', 'insurance_due_date']:
                                parsed_date = self.parse_date(str(value))
                                if parsed_date:
                                    car_data[model_field] = parsed_date
                                    # 如果是上牌时间，同时设置registration_date字段
                                    if model_field == 'registration_date':
                                        car_data['registration_date'] = parsed_date
                                        car_data['first_registration'] = str(value)  # 保存原始文本
                            
                            elif model_field == 'publish_date':
                                try:
                                    if isinstance(value, str):
                                        parsed_date = parse_date(value)
                                        if parsed_date:
                                            car_data[model_field] = datetime.combine(parsed_date, datetime.min.time())
                                except:
                                    continue
                            
                            elif model_field == 'transfer_count':
                                parsed_count = self.parse_transfer_count(value)
                                if parsed_count is not None:
                                    car_data[model_field] = parsed_count
                            
                            elif model_field in ['nedc_range', 'cltc_range']:
                                try:
                                    if 'km' in str(value):
                                        value = str(value).replace('km', '')
                                    num = ''.join(filter(str.isdigit, str(value)))
                                    if num:
                                        car_data[model_field] = int(num)
                                except:
                                    continue
                            
                            else:
                                car_data[model_field] = str(value).strip()

                    # 直接处理特殊字段
                    if idx == 0:
                        self.stdout.write("\nProcessing special fields for first row:")
                        self.stdout.write(f"Available columns: {[col for col in df.columns]}")

                    # 处理变速箱
                    transmission_col = next((col for col in df.columns if '变' in col and '速' in col and '箱' in col), None)
                    if transmission_col:
                        value = row[transmission_col]
                        if idx == 0:
                            self.stdout.write(f"\nProcessing transmission:")
                            self.stdout.write(f"Found column: {transmission_col}")
                            self.stdout.write(f"Raw value: {value}")
                        if not pd.isna(value) and value != '-' and str(value).strip():
                            car_data['transmission'] = str(value).strip()
                            if idx == 0:
                                self.stdout.write(f"Setting transmission to: {car_data['transmission']}")

                    # 处理发动机
                    engine_col = next((col for col in df.columns if '发' in col and '动' in col and '机' in col), None)
                    if engine_col:
                        value = row[engine_col]
                        if idx == 0:
                            self.stdout.write(f"\nProcessing engine:")
                            self.stdout.write(f"Found column: {engine_col}")
                            self.stdout.write(f"Raw value: {value}")
                        if not pd.isna(value) and value != '-' and str(value).strip():
                            car_data['engine'] = str(value).strip()
                            if idx == 0:
                                self.stdout.write(f"Setting engine to: {car_data['engine']}")

                    # 处理所在地
                    location_col = next((col for col in df.columns if '所' in col and '在' in col and '地' in col), None)
                    if location_col:
                        value = row[location_col]
                        if idx == 0:
                            self.stdout.write(f"\nProcessing location:")
                            self.stdout.write(f"Found column: {location_col}")
                            self.stdout.write(f"Raw value: {value}")
                        if not pd.isna(value) and value != '-' and str(value).strip():
                            car_data['location'] = str(value).strip()
                            if idx == 0:
                                self.stdout.write(f"Setting location to: {car_data['location']}")

                    # 处理排量
                    displacement_col = next((col for col in df.columns if '排' in col and '量' in col), None)
                    if displacement_col:
                        value = row[displacement_col]
                        if idx == 0:
                            self.stdout.write(f"\nProcessing displacement:")
                            self.stdout.write(f"Found column: {displacement_col}")
                            self.stdout.write(f"Raw value: {value}")
                        if not pd.isna(value) and value != '-' and str(value).strip():
                            car_data['displacement'] = str(value).strip()
                            if idx == 0:
                                self.stdout.write(f"Setting displacement to: {car_data['displacement']}")

                    # 确保必填字段有值
                    if not car_data.get('title'):
                        raise ValueError('车辆名称不能为空')
                    if not car_data.get('price'):
                        car_data['price'] = Decimal('0.00')
                    if not car_data.get('detail_url'):
                        raise ValueError('详情链接不能为空')
                    if not car_data.get('location'):
                        # 尝试从详情中提取地址
                        detail = car_data.get('detail', '')
                        if detail and '／' in detail:
                            parts = detail.split('／')
                            if len(parts) >= 3:
                                car_data['location'] = parts[2].split('／')[0]
                            else:
                                car_data['location'] = '未知'
                        else:
                            car_data['location'] = '未知'

                    # 创建品牌和车型
                    brand_name, model_name = self.clean_brand_model(car_data['title'])
                    brand, _ = Brand.objects.get_or_create(name=brand_name)
                    car_model, _ = CarModel.objects.get_or_create(
                        brand=brand,
                        name=model_name
                    )

                    # 打印第一条记录的数据用于调试
                    if idx == 0:
                        self.stdout.write("\nFirst record data to be saved:")
                        for field, value in sorted(car_data.items()):
                            self.stdout.write(f"{field}: {value}")

                    # 创建二手车记录
                    car_data['car_model'] = car_model
                    car = UsedCar.objects.create(**car_data)

                    # 验证保存的数据
                    if idx == 0:
                        self.stdout.write("\nVerifying saved data for first record:")
                        saved_car = UsedCar.objects.get(id=car.id)
                        self.stdout.write(f"transmission: {saved_car.transmission}")
                        self.stdout.write(f"engine: {saved_car.engine}")
                        self.stdout.write(f"location: {saved_car.location}")
                        self.stdout.write(f"displacement: {saved_car.displacement}")

                    success_count += 1
                    if success_count % 100 == 0:
                        self.stdout.write(f'Successfully imported {success_count} cars...')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row {idx + 1}: {str(e)}'))
                    error_count += 1
                    continue

            self.stdout.write(self.style.SUCCESS(
                f'Import completed. Successfully imported {success_count} cars. '
                f'Failed to import {error_count} cars.'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading Excel file: {str(e)}'))