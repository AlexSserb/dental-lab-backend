from django.urls import path

from . import views

urlpatterns = [
    path("operations-for-tech/", views.get_operations_for_tech, name="operations-for-tech"),
    path("operations-for-product/<str:product_id>/", views.get_operations_for_product, name="operations-for-product"),
    path("operation/<str:operation_id>", views.update_operation_status, name="operation"),
    path("operation-statuses/", views.OperationStatusesList.as_view(), name="operation-statuses"),
    path(
        "operations-for-schedule/<str:date_start>/<str:tech_email>",
        views.get_operations_for_tech_schedule,
        name="operations-for-tech-schedule",
    ),
    path(
        "operations-for-schedule/<str:date_start>",
        views.get_operations_for_schedule,
        name="operations-for-schedule",
    ),
    path("update-operation", views.update_operation, name="update-operation"),
    path("assign-operation", views.assign_operation, name="operation-assignment"),
    path("plan", views.generate_optimized_plan, name="generate-optimized-plan"),
    path("plan/apply", views.apply_optimized_plan, name="apply-optimized-plan"),
    path("assign-operations/order", views.assign_order_operations, name="assign-operations-order"),
]
