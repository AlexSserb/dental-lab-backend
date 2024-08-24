from django.urls import path

from . import views

urlpatterns = [
    path("operation-types/", views.OperationTypeList.as_view(), name="operation-types"),
    path("operation-type/<str:pk>/", views.OperationTypeDetail.as_view(), name="operation-type"),
    path("product-types/", views.ProductTypeList.as_view(), name="product-types"),
    path("orders-for-physician/", views.get_orders_for_physician, name="orders-for-physician"),
    path("orders/<int:year>/<int:month>/", views.get_orders, name="orders"),
    path("create-order/", views.create_order, name="create-order"),
    path("confirm-order/", views.confirm_order, name="confirm-order"),
    path("products/<str:order_id>/", views.get_products_for_order, name="products-for-order"),
    path("products/operations/<str:order_id>/", views.get_products_with_operations, name="products-with-operations"),
    path("operations-for-tech/", views.get_operations_for_tech, name="operations-for-tech"),
    path("operations-for-product/<str:product_id>/", views.get_operations_for_product, name="operations-for-product"),
    path("operation/<str:pk>/", views.OperationDetail.as_view(), name="operation"),
    path("operation-statuses/", views.OperationStatusesList.as_view(), name="operation-statuses"),
    path("order-statuses/", views.OrderStatusesList.as_view(), name="order-statuses"),
    path(
        "operations-for-schedule/<str:user_email>/<str:date>",
        views.get_operations_for_schedule,
        name="operations-for-schedule",
    ),
    path(
        "operation-exec-start/<str:id>/<str:exec_start>",
        views.set_operation_exec_start,
        name="set-operation-exec-start",
    ),
    path("assign-operation/", views.assign_operation, name="operation-assignment"),
    path("set-order-status/<str:id>", views.set_order_status, name="set-order-status"),
]
