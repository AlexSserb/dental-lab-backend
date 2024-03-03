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
    list_display = ('name', 'cost', 'product_info')
    fieldsets = (
        (None, { 'fields': ('name', 'cost', 'product_info'), }),
    )

admin.site.register(ProductType, ProductTypeAdmin)

admin.site.register(OperationStatus)
admin.site.register(ProductStatus)
admin.site.register(OrderStatus)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'order_date', 'discount']

admin.site.register(Order, OrderAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_type', 'product_status', 'order', 'amount']

admin.site.register(Product, ProductAdmin)


class OperationAdmin(admin.ModelAdmin):
    list_display = ['operation_type', 'operation_status', 'product', 'tech']

admin.site.register(Operation, OperationAdmin)
