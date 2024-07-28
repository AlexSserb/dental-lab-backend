from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from .models import *


class BaseModelAdmin(admin.ModelAdmin):
    exclude = ("is_active",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

    def delete_model(self, request, obj):
        obj.is_active = False
        obj.save()


admin.site.register(OperationType, BaseModelAdmin)


class OperationTypeProductTypeInline(admin.TabularInline):
    verbose_name = "операция для выполнения изделия"
    verbose_name_plural = "операции для выполнения изделия"
    model = ProductType.operation_types.through
    extra = 1


class ProductTypeAdmin(BaseModelAdmin):
    inlines = (OperationTypeProductTypeInline,)
    list_display = ("name", "cost")
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "cost"),
            },
        ),
    )


admin.site.register(ProductType, ProductTypeAdmin)

admin.site.register(OperationStatus, BaseModelAdmin)
admin.site.register(ProductStatus, BaseModelAdmin)
admin.site.register(OrderStatus, BaseModelAdmin)


class OrderAdmin(BaseModelAdmin):
    list_display = ["user", "status", "order_date", "discount"]


admin.site.register(Order, OrderAdmin)


class ProductAdmin(BaseModelAdmin):
    list_display = ["product_type", "product_status", "order", "amount"]


admin.site.register(Product, ProductAdmin)


class OperationAdmin(BaseModelAdmin):
    list_display = ["operation_type", "operation_status", "product", "tech"]


admin.site.register(Operation, OperationAdmin)
