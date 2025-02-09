from django.urls import path

from . import views

urlpatterns = [
    path("orders-for-physician/", views.get_orders_for_physician, name="orders-for-physician"),
    path("orders/<int:year>/<int:month>/", views.get_orders, name="orders"),
    path("create-order/", views.create_order, name="create-order"),
    path("confirm-order/", views.confirm_order, name="confirm-order"),
    path("order-statuses/", views.OrderStatusesList.as_view(), name="order-statuses"),
    path("set-order-status/<str:id>", views.set_order_status, name="set-order-status"),
]
