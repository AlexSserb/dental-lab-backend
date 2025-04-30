from django.contrib import admin

from core.admin import BaseModelAdmin, BaseStatusAdmin
from works.models import Work, WorkStatus, WorkType


class OperationTypeWorkTypeInline(admin.TabularInline):
    verbose_name = "операция для выполнения работы"
    verbose_name_plural = "операции для выполнения работы"
    model = WorkType.operation_types.through
    ordering = ("ordinal_number",)
    extra = 1


class WorkTypeAdmin(BaseModelAdmin):
    inlines = (OperationTypeWorkTypeInline,)
    list_display = ("name", "cost")
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "cost"),
            },
        ),
    )


admin.site.register(WorkType, WorkTypeAdmin)

admin.site.register(WorkStatus, BaseStatusAdmin)


class WorkAdmin(BaseModelAdmin):
    list_display = ["work_type", "work_status", "order", "amount"]


admin.site.register(Work, WorkAdmin)
