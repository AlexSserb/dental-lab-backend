from django.contrib import admin

from api.admin import BaseModelAdmin
from api.models import OperationType, Order, Product, Operation

admin.site.register(OperationType, BaseModelAdmin)


class OrderAdmin(BaseModelAdmin):
    list_display = ["user", "status", "order_date", "discount"]


class OperationAdmin(BaseModelAdmin):
    list_display = ["operation_type", "operation_status", "product", "tech"]


class ProductAdmin(BaseModelAdmin):
    list_display = ["product_type", "product_status", "order", "amount"]


admin.site.register(Order, OrderAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Operation, OperationAdmin)
