from django.urls import path

import orders.views
from . import views

urlpatterns = [
    path("operation-types/", views.OperationTypeList.as_view(), name="operation-types"),
    path("operation-type/<str:pk>/", views.OperationTypeDetail.as_view(), name="operation-type"),
    path("operations-for-tech/", views.get_operations_for_tech, name="operations-for-tech"),
    path("operations-for-product/<str:product_id>/", views.get_operations_for_product, name="operations-for-product"),
    path("operation/<str:pk>/", views.OperationDetail.as_view(), name="operation"),
    path("operation-statuses/", views.OperationStatusesList.as_view(), name="operation-statuses"),
    path(
        "operations-for-schedule/<str:date>/<str:user_email>",
        views.get_operations_for_schedule,
        name="operations-for-schedule",
    ),
    path(
        "operation-exec-start/<str:id>/<str:exec_start>",
        views.set_operation_exec_start,
        name="set-operation-exec-start",
    ),
    path("assign-operation/", views.assign_operation, name="operation-assignment"),
]
