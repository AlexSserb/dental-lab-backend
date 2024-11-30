from django.contrib import admin

from api.admin.base_model_admin import BaseModelAdmin
from api.models import ProductType


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
