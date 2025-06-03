from django import forms
from .models import Chart

class ChartForm(forms.ModelForm):
    """图表表单"""
    class Meta:
        model = Chart
        fields = ['title', 'description', 'chart_type', 'data_type', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入图表标题'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入图表描述'}),
            'chart_type': forms.Select(attrs={'class': 'form-control'}),
            'data_type': forms.Select(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': '图表标题',
            'description': '图表描述',
            'chart_type': '图表类型',
            'data_type': '数据类型',
            'is_public': '公开图表',
        }