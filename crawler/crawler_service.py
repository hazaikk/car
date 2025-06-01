import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
from django.utils import timezone
from .models import CrawlerTask, UsedCar, Brand, CarModel
import re
from decimal import Decimal, InvalidOperation

class CarCrawlerService:
    """二手车爬虫服务"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
        }
        
        # 初始化 requests session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # 基础URL
        self.base_url = 'https://www.che168.com/china/a00-a0-a-b-suva0-suva-suvb/0_5/a3_8msdgscncgpi1ltocsp'
        self.max_retries = 30
        
    def extract_price(self, price_str):
        """提取价格数字"""
        if not price_str or price_str == "无价格":
            return None
        
        # 移除非数字字符，保留小数点
        price_clean = re.sub(r'[^\d.]', '', price_str)
        try:
            return Decimal(price_clean)
        except (InvalidOperation, ValueError):
            return None
    
    def parse_brand_and_model(self, car_name):
        """解析品牌和车型"""
        # 简单的品牌识别逻辑，可以根据需要扩展
        common_brands = [
            '奥迪', '宝马', '奔驰', '大众', '丰田', '本田', '日产', '马自达', '现代', '起亚',
            '福特', '雪佛兰', '别克', '凯迪拉克', '沃尔沃', '路虎', '捷豹', '保时捷', '法拉利',
            '兰博基尼', '玛莎拉蒂', '阿斯顿马丁', '宾利', '劳斯莱斯', '特斯拉', '蔚来', '理想',
            '小鹏', '比亚迪', '吉利', '长城', '奇瑞', '长安', '红旗', '五菱', '宝骏'
        ]
        
        brand_name = None
        for brand in common_brands:
            if brand in car_name:
                brand_name = brand
                break
        
        if not brand_name:
            # 如果没有匹配到已知品牌，取第一个词作为品牌
            parts = car_name.split()
            brand_name = parts[0] if parts else '未知品牌'
        
        # 获取或创建品牌
        brand, created = Brand.objects.get_or_create(
            name=brand_name,
            defaults={'description': f'通过爬虫自动创建的品牌: {brand_name}'}
        )
        
        # 获取或创建车型
        car_model, created = CarModel.objects.get_or_create(
            brand=brand,
            name=car_name,
            defaults={}
        )
        
        return car_model
    
    def crawl_cars(self, task_id, target_count=100):
        """爬取二手车数据"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            task.status = 'running'
            task.start_time = timezone.now()
            task.save()
            
            current_page = 1
            count = 0
            car_data = []
            items_per_page = 40
            
            while count < target_count:
                # 构建当前页的URL
                current_url = f"{self.base_url}{current_page}exx0a1/"
                print(f"正在爬取第{current_page}页: {current_url}")
                
                retries = 0
                cars = []
                
                while retries < self.max_retries:
                    try:
                        # 获取当前页面内容
                        response = self.session.get(current_url, headers=self.headers, timeout=10)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 获取所有的车辆卡片
                        cars = soup.select('li.cards-li.list-photo-li')
                        
                        if cars:
                            break  # 如果成功获取到数据，跳出重试循环
                        else:
                            print(f"未能获取到车辆数据，正在重试第 {retries + 1} 次...")
                            retries += 1
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"请求失败: {e}")
                        retries += 1
                        time.sleep(2)
                
                if retries == self.max_retries:
                    print("达到最大重试次数，停止抓取。")
                    break
                
                # 当前页的计数
                current_page_count = 0
                
                for car in cars:
                    if count >= target_count:
                        break
                    
                    try:
                        car_name = car.select_one('.card-name').get_text(strip=True) if car.select_one('.card-name') else "未知车型"
                        car_details = car.select_one('.cards-unit').get_text(strip=True) if car.select_one('.cards-unit') else "无详情"
                        car_price = car.select_one('.cards-price-box .pirce em').get_text(strip=True) if car.select_one('.cards-price-box .pirce em') else "无价格"
                        
                        # 获取详情页链接
                        detail_link = car.find('a', class_='carinfo')['href'] if car.find('a', class_='carinfo') else None
                        if not detail_link or not detail_link.startswith("/dealer"):
                            print(f"跳过车辆 {car_name}，因为详情链接无效")
                            continue
                        
                        detail_url = 'https://www.che168.com' + detail_link
                        
                        # 请求详情页
                        detail_response = self.session.get(detail_url, headers=self.headers, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        
                        # 解析详情页信息
                        details = {}
                        for li in detail_soup.select('#nav1 .basic-item-ul li'):
                            item_name_tag = li.select_one('.item-name')
                            item_name = item_name_tag.get_text(strip=True) if item_name_tag else "未知项"
                            item_value = li.get_text(strip=True).replace(item_name, '').strip() if item_name_tag else "无信息"
                            details[item_name] = item_value
                        
                        # 解析品牌和车型
                        car_model = self.parse_brand_and_model(car_name)
                        
                        # 提取价格
                        price = self.extract_price(car_price)
                        
                        # 存储到临时数据
                        car_info = {
                            '车辆名称': car_name,
                            '车辆详情': car_details,
                            '价格': car_price,
                            '详情链接': detail_url,
                            **details
                        }
                        car_data.append(car_info)
                        
                        print(f"抓取 {car_name} 成功")
                        count += 1
                        current_page_count += 1
                        
                        # 更新任务进度
                        task.actual_count = count
                        task.crawled_data = car_data
                        task.save()
                        
                        # 如果当前页已经抓取到足够数据，直接翻页
                        if current_page_count >= items_per_page:
                            break
                            
                    except Exception as e:
                        print(f"抓取失败: {e}")
                        continue
                
                current_page += 1
            
            # 任务完成
            task.status = 'completed'
            task.end_time = timezone.now()
            task.actual_count = count
            task.crawled_data = car_data
            task.save()
            
            return True, f"成功爬取 {count} 条数据"
            
        except Exception as e:
            # 任务失败
            task.status = 'failed'
            task.end_time = timezone.now()
            task.error_message = str(e)
            task.save()
            return False, str(e)
    
    def import_to_database(self, task_id):
        """将爬取的数据导入到数据库"""
        try:
            task = CrawlerTask.objects.get(id=task_id)
            if not task.crawled_data:
                return False, "没有可导入的数据"
            
            imported_count = 0
            for car_info in task.crawled_data:
                try:
                    # 解析品牌和车型
                    car_model = self.parse_brand_and_model(car_info.get('车辆名称', ''))
                    
                    # 提取价格
                    price = self.extract_price(car_info.get('价格', ''))
                    
                    # 创建二手车记录
                    used_car = UsedCar.objects.create(
                        car_model=car_model,
                        title=car_info.get('车辆名称', ''),
                        price=price,
                        detail_url=car_info.get('详情链接', ''),
                        mileage_text=car_info.get('表显里程', ''),
                        location=car_info.get('所\xa0\xa0在\xa0\xa0地', ''),
                        accident_check=car_info.get('事故排查', ''),
                        first_registration=car_info.get('首次上牌', ''),
                        annual_inspection=car_info.get('年检到期', ''),
                        insurance_expiry=car_info.get('保险到期', ''),
                        transfer_count=car_info.get('过户次数', ''),
                        usage_nature=car_info.get('使用性质', ''),
                        displacement=car_info.get('排\xa0\xa0\xa0\xa0\xa0\xa0\xa0量', ''),
                        gearbox=car_info.get('变\xa0\xa0速\xa0\xa0箱', ''),
                        fuel_type=car_info.get('燃料类型', ''),
                        drive_type=car_info.get('驱动方式', ''),
                        emission_standard=car_info.get('排放标准', ''),
                    )
                    imported_count += 1
                    
                except Exception as e:
                    print(f"导入数据失败: {e}")
                    continue
            
            return True, f"成功导入 {imported_count} 条数据"
            
        except Exception as e:
            return False, str(e)