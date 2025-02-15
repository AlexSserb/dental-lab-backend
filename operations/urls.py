from django.urls import path

import orders.views
from . import views

urlpatterns = [
    path("operations-for-tech/", views.get_operations_for_tech, name="operations-for-tech"),
    path("operations-for-product/<str:product_id>/", views.get_operations_for_product, name="operations-for-product"),
    path("operation/<str:operation_id>", views.update_operation_status, name="operation"),
    path("operation-statuses/", views.OperationStatusesList.as_view(), name="operation-statuses"),
    path(
        "operations-for-schedule/<str:date_start>/<str:tech_email>",
        views.get_operations_for_schedule,
        name="operations-for-schedule",
    ),
    path(
        "operation-exec-start/<str:operation_id>/<str:exec_start>",
        views.set_operation_exec_start,
        name="set-operation-exec-start",
    ),
    path("assign-operation", views.assign_operation, name="operation-assignment"),
]
