# 🚗 汽车之家数据可视化与智能分析平台

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

*一个基于Django的现代化汽车数据可视化与智能分析平台*

[功能特性](#-功能特性) • [技术栈](#-技术栈) • [快速开始](#-快速开始) • [项目结构](#-项目结构) • [使用指南](#-使用指南)

</div>

## 📋 项目简介

汽车之家数据可视化与智能分析平台是一个专为汽车行业打造的数据分析系统，集成了数据爬取、可视化展示、智能分析和用户管理等功能。平台支持多维度的汽车数据分析，为个人用户、企业用户和系统管理员提供不同层次的服务。

## ✨ 功能特性

### 🎯 核心功能
- **📊 数据可视化**: 丰富的图表展示，包括品牌分布、价格区间、地区分析等
- **🔍 智能分析**: 基于机器学习的汽车推荐和趋势分析
- **🔄 数据爬取**: 自动化的汽车数据采集和更新
- **📈 竞品对比**: 多维度车型对比分析
- **📤 数据导出**: 支持Excel、图片等多种格式导出
- **🔐 用户管理**: 多角色权限管理系统

### 👥 用户角色
- **普通用户**: 浏览数据、筛选条件、导出图表
- **企业用户**: 高级分析功能、竞品对比、API接口
- **系统管理员**: 用户管理、系统配置、数据监控

## 🛠 技术栈

### 后端技术
- **框架**: Django 4.2
- **数据库**: SQLite3 / MySQL
- **数据处理**: Pandas, NumPy
- **机器学习**: Scikit-learn
- **数据可视化**: Matplotlib, Seaborn
- **网络爬虫**: Requests, BeautifulSoup4

### 前端技术
- **UI框架**: Bootstrap 5
- **图表库**: Chart.js, ECharts
- **管理界面**: Django SimpleUI
- **用户认证**: Django Allauth

### 开发工具
- **环境管理**: Python-dotenv
- **图像处理**: Pillow
- **API开发**: Django REST Framework

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Django 4.2+
- 推荐使用虚拟环境

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/cardata_platform.git
cd cardata_platform
```

2. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **创建超级用户**
```bash
python manage.py createsuperuser
```

6. **启动服务**
```bash
python manage.py runserver
```

7. **访问应用**
- 前台地址: http://127.0.0.1:8000/
- 管理后台: http://127.0.0.1:8000/admin/

## 📁 项目结构

```
cardata_platform/
├── 📁 accounts/           # 用户账户管理
├── 📁 analysis/            # 数据分析模块
├── 📁 analysis_records/    # 分析记录
├── 📁 analysis_results/    # 分析结果
├── 📁 api/                 # API接口
├── 📁 car_analysis/        # 汽车分析
├── 📁 car_api/             # 汽车API
├── 📁 crawler/             # 数据爬虫
├── 📁 dashboard/           # 仪表板
├── 📁 data_analysis/       # 数据分析
├── 📁 visualization/       # 数据可视化
├── 📁 templates/           # 模板文件
├── 📁 static/              # 静态资源
├── 📁 media/               # 媒体文件
├── 📄 manage.py            # Django管理脚本
├── 📄 requirements.txt     # 项目依赖
└── 📄 README.md            # 项目说明
```

## 📖 使用指南

### 数据可视化
1. 访问首页查看汽车数据概览
2. 使用筛选功能按品牌、价格、地区等条件过滤数据
3. 查看各类图表分析，包括:
   - 品牌分布饼图
   - 价格区间柱状图
   - 地区销量分析
   - 时间趋势图

### 智能分析
1. 进入分析模块
2. 选择分析类型和参数
3. 查看智能推荐结果
4. 导出分析报告

### 数据管理
1. 管理员登录后台
2. 配置爬虫任务
3. 监控数据质量
4. 管理用户权限

## 🔧 配置说明

### 环境变量
创建 `.env` 文件并配置以下变量:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

### 数据库配置
- 开发环境: SQLite3 (默认)
- 生产环境: MySQL (推荐)

## 📊 核心用例

| 用例名称 | 简要说明 |
|---------|----------|
| 浏览数据图表 | 用户可查看各类汽车销售、评论、评分等相关的可视化图表 |
| 筛选数据条件 | 用户可按品牌、价格区间、地区等多维条件筛选需要的数据 |
| 导出图表或数据 | 支持将当前可视化图表或数据以 Excel、图像等格式导出 |
| 智能分析推荐 | 系统通过分析用户偏好或历史数据，智能推荐可能关注的车型或信息 |
| 竞品对比分析 | 企业用户可对多个车型进行横向对比，查看参数、销量、口碑等差异 |
| 通过API获取数据 | 企业用户可调用系统提供的API接口，获取分析数据以集成至第三方系统 |
| 用户管理 | 管理员可管理用户注册信息、权限等级、角色归属等 |
| 系统配置 | 管理员可配置系统运行参数，如分析维度、图表类型等 |
| 数据监控与维护 | 管理员可查看数据入库、任务调度状态，进行数据修复与手动调度 |

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

**软件工程课程设计项目**

- 项目类型: 汽车数据可视化与智能分析平台
- 开发语言: Python
- 框架: Django
- 完成时间: 2025年6月

## 📞 联系方式

如有问题或建议，请通过以下方式联系:

- 📧 Email: 3505318655@qq.com
- 🐛 Issues: [GitHub Issues](https://github.com/hazaikk/car/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星标！**

*Made with ❤️ for Software Engineering Course*

</div>

