from django.contrib import admin

from core.admin import BaseStatusAdmin, BaseModelAdmin
from orders.models import OrderStatus, Order

admin.site.register(OrderStatus, BaseStatusAdmin)


class OrderAdmin(BaseModelAdmin):
    list_display = ["user", "status", "order_date", "discount"]


admin.site.register(Order, OrderAdmin)
