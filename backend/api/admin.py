from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from .models import *


admin.site.register(OperationType)

class OperationTypeProductTypeInline(admin.TabularInline):
    verbose_name = 'операция для выполнения изделия'
    verbose_name_plural = 'операции для выполнения изделия'
    model = ProductType.operation_types.through
    extra = 1

class ProductTypeAdmin(admin.ModelAdmin):
    inlines = (
        OperationTypeProductTypeInline,
    )
    fieldsets = (
        (None, { 'fields': ('name',), }),
    )


admin.site.register(ProductType, ProductTypeAdmin)

admin.site.register(OperationStatus)
admin.site.register(ProductStatus)
admin.site.register(OrderStatus)
admin.site.register(Order)
admin.site.register(Product)
admin.site.register(Tooth)
admin.site.register(Operation)
