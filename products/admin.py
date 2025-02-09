from django.contrib import admin

from core.admin import BaseModelAdmin, BaseStatusAdmin
from products.models import Product, ProductStatus, ProductType


class OperationTypeProductTypeInline(admin.TabularInline):
    verbose_name = "операция для выполнения изделия"
    verbose_name_plural = "операции для выполнения изделия"
    model = ProductType.operation_types.through
    ordering = ("ordinal_number",)
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

admin.site.register(ProductStatus, BaseStatusAdmin)


class ProductAdmin(BaseModelAdmin):
    list_display = ["product_type", "product_status", "order", "amount"]


admin.site.register(Product, ProductAdmin)
