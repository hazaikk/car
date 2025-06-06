# Generated by Django 4.2.10 on 2025-05-31 05:02

import analysis_results.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100, verbose_name="标题")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="描述"),
                ),
                (
                    "analysis_type",
                    models.CharField(
                        choices=[
                            ("price_by_brand", "品牌价格分析"),
                            ("price_by_region", "地区价格分析"),
                            ("price_by_year", "年份价格分析"),
                            ("price_by_mileage", "里程价格分析"),
                            ("count_by_brand", "品牌数量分析"),
                            ("count_by_region", "地区数量分析"),
                            ("count_by_fuel", "燃料类型分析"),
                            ("count_by_transmission", "变速箱类型分析"),
                            ("count_by_color", "车身颜色分析"),
                        ],
                        max_length=50,
                        verbose_name="分析类型",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=analysis_results.models.analysis_image_path,
                        verbose_name="分析图片",
                    ),
                ),
                (
                    "data_file",
                    models.FileField(
                        upload_to=analysis_results.models.analysis_data_path,
                        verbose_name="数据文件",
                    ),
                ),
                (
                    "filter_params",
                    models.JSONField(blank=True, null=True, verbose_name="筛选参数"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "分析结果",
                "verbose_name_plural": "分析结果",
                "ordering": ["-created_at"],
            },
        ),
    ]
