from django.contrib import admin

from core.admin import BaseModelAdmin, BaseStatusAdmin
from operations.models import OperationStatus, Operation, OperationType

admin.site.register(OperationStatus, BaseStatusAdmin)

admin.site.register(OperationType, BaseModelAdmin)


class OperationAdmin(BaseModelAdmin):
    list_display = ["operation_type", "operation_status", "product", "tech"]


admin.site.register(Operation, OperationAdmin)
