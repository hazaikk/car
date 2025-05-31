from django import forms
from django.core.exceptions import ValidationError
from .models import CrawlerTask

class CrawlerTaskForm(forms.ModelForm):
    """爬虫任务表单"""
    
    class Meta:
        model = CrawlerTask
        fields = ['name', 'target_count', 'start_page', 'end_page', 'delay_seconds', 'search_keyword']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '请输入任务名称'}),
            'target_count': forms.NumberInput(attrs={'min': 1, 'max': 1000, 'placeholder': '目标爬取数量'}),
            'start_page': forms.NumberInput(attrs={'min': 1, 'placeholder': '起始页码'}),
            'end_page': forms.NumberInput(attrs={'min': 1, 'placeholder': '终止页码'}),
            'delay_seconds': forms.NumberInput(attrs={'min': 0.5, 'max': 10, 'step': 0.5, 'placeholder': '请求间隔(秒)'}),
            'search_keyword': forms.TextInput(attrs={'placeholder': '搜索关键词(可选)'}),
        }
        help_texts = {
            'target_count': '目标爬取的车辆数量（建议不超过1000）',
            'start_page': '爬取起始页码（从1开始）',
            'end_page': '爬取终止页码（必须大于起始页码）',
            'delay_seconds': '每次请求间隔时间（秒），建议1-3秒',
            'search_keyword': '搜索关键词（可选），如品牌名称或车型',
        }
    
    def clean(self):
        """表单验证"""
        cleaned_data = super().clean()
        start_page = cleaned_data.get('start_page')
        end_page = cleaned_data.get('end_page')
        target_count = cleaned_data.get('target_count')
        
        # 验证页码范围
        if start_page and end_page:
            if start_page >= end_page:
                raise ValidationError('终止页码必须大于起始页码')
            
            # 检查页码范围是否合理
            page_range = end_page - start_page + 1
            if page_range > 100:
                raise ValidationError('页码范围不能超过100页，请缩小范围')
        
        # 验证目标数量
        if target_count:
            if target_count > 1000:
                raise ValidationError('目标爬取数量不能超过1000')
            if target_count < 1:
                raise ValidationError('目标爬取数量必须大于0')
        
        return cleaned_data
    
    def clean_name(self):
        """验证任务名称"""
        name = self.cleaned_data.get('name')
        if name:
            # 检查是否存在同名任务（排除当前编辑的任务）
            existing_tasks = CrawlerTask.objects.filter(name=name)
            if self.instance.pk:
                existing_tasks = existing_tasks.exclude(pk=self.instance.pk)
            
            if existing_tasks.exists():
                raise ValidationError('已存在同名的爬虫任务，请使用不同的名称')
        
        return name