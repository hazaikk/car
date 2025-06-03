import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import time

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
}

# 初始化 requests session
session = requests.Session()
retry_strategy = Retry(
    total=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# 基础URL和初始页码
base_url = 'https://www.che168.com/china/a00-a0-a-b-suva0-suva-suvb/0_5/a3_8msdgscncgpi1ltocsp'
current_page = 1  # 当前页码
max_count = 5000  # 总共要爬取的数据量
items_per_page = 40  # 每页抓取的数据条数
count = 0  # 当前抓取的数据总量
max_retries = 30  # 最大重试次数

# 存储数据的列表
car_data = []

while count < max_count:
    # 构建当前页的URL
    current_url = f"{base_url}{current_page}exx0a1/"
    print(current_url)
    retries = 0  # 重试计数
    while retries < max_retries:
        try:
            # 获取当前页面内容
            response = session.get(current_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 获取所有的车辆卡片
            cars = soup.select('li.cards-li.list-photo-li')

            if cars:
                break  # 如果成功获取到数据，跳出重试循环
            else:
                print(f"未能获取到车辆数据，正在重试第 {retries + 1} 次...")
                retries += 1
                time.sleep(2)  # 等待2秒后重试

        except Exception as e:
            print(f"请求失败: {e}")
            retries += 1
            time.sleep(2)  # 等待2秒后重试

    if retries == max_retries:
        print("达到最大重试次数，停止抓取。")
        break

    # 当前页的计数
    current_page_count = 0

    for car in cars:
        if count >= max_count:
            break  # 达到设定数量后停止

        # 获取卡片信息
        try:
            car_name = car.select_one('.card-name').get_text(strip=True) if car.select_one('.card-name') else "未知车型"
            car_details = car.select_one('.cards-unit').get_text(strip=True) if car.select_one(
                '.cards-unit') else "无详情"
            car_price = car.select_one('.cards-price-box .pirce em').get_text(strip=True) if car.select_one(
                '.cards-price-box .pirce em') else "无价格"

            # 获取详情页链接
            detail_link = car.find('a', class_='carinfo')['href'] if car.find('a', class_='carinfo') else None
            if not detail_link or not detail_link.startswith("/dealer"):
                print(f"跳过车辆 {car_name}，因为详情链接无效")
                continue

            detail_url = 'https://www.che168.com' + detail_link

            # 请求详情页
            detail_response = session.get(detail_url, headers=headers, timeout=10)
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

            # 解析详情页信息
            details = {}
            for li in detail_soup.select('#nav1 .basic-item-ul li'):
                item_name_tag = li.select_one('.item-name')
                item_name = item_name_tag.get_text(strip=True) if item_name_tag else "未知项"
                item_value = li.get_text(strip=True).replace(item_name, '').strip() if item_name_tag else "无信息"
                details[item_name] = item_value

            # 存储数据
            car_data.append({
                '车辆名称': car_name,
                '车辆详情': car_details,
                '价格': car_price,
                '详情链接': detail_url,
                **details  # 将详细信息字典展开为表中的各列
            })

            print(f"抓取 {car_name} 成功")
            count += 1
            current_page_count += 1  # 增加当前页计数

            # 为了避免频繁请求而被封，增加延时
            # time.sleep(1)

            # 如果当前页已经抓取到50条，直接翻页
            if current_page_count >= items_per_page:
                break  # 跳出当前循环进入下一页

        except Exception as e:
            print(f"抓取失败: {e}")

    current_page += 1  # 进入下一页

# 将数据保存到Excel文件
df = pd.DataFrame(car_data)
df.to_excel('二手车数据1.xlsx', index=False)
print("数据已保存到 '二手车数据.xlsx'")
