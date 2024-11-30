from django.contrib import admin

from api.admin.base_model_admin import BaseModelAdmin
from api.models import OperationStatus, ProductStatus, OrderStatus


class BaseStatusAdmin(BaseModelAdmin):
    exclude = ("number", "is_active")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(OperationStatus, BaseStatusAdmin)
admin.site.register(ProductStatus, BaseStatusAdmin)
admin.site.register(OrderStatus, BaseStatusAdmin)
