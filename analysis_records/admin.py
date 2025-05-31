from django.contrib import admin
from .models import AnalysisRecord

@admin.register(AnalysisRecord)
class AnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'analysis_type', 'created_at', 'short_parameters', 'short_summary')
    list_filter = ('analysis_type', 'user', 'created_at')
    search_fields = ('analysis_type', 'user__username', 'parameters', 'result_summary')
    readonly_fields = ('user', 'analysis_type', 'parameters', 'result_summary', 'created_at')

    def short_parameters(self, obj):
        # 简短显示参数，避免过长
        params_str = str(obj.parameters)
        return (params_str[:75] + '...') if len(params_str) > 75 else params_str
    short_parameters.short_description = '分析参数'

    def short_summary(self, obj):
        # 简短显示结果摘要
        summary_str = str(obj.result_summary)
        return (summary_str[:75] + '...') if len(summary_str) > 75 else summary_str
    short_summary.short_description = '结果摘要'

    def has_add_permission(self, request):
        # 通常分析记录由系统自动创建，不允许手动添加
        return False

    def has_change_permission(self, request, obj=None):
        # 可以允许查看，但不允许修改记录
        return False # 或者 return True 如果希望管理员能编辑

    # 如果需要，可以自定义删除权限
    # def has_delete_permission(self, request, obj=None):
    # return True