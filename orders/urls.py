from django.urls import path

from . import views

urlpatterns = [
    path("orders-for-physician/", views.get_orders_for_physician, name="orders-for-physician"),
    path("orders/<int:year>/<int:month>/", views.get_orders, name="orders"),
    path("create-order/", views.create_order, name="create-order"),
    path("load-files/<str:order_id>", views.load_order_files, name="load-files"),
    path("download-file/<str:file_id>", views.download_file, name="download-file"),
    path("confirm-order/", views.confirm_order, name="confirm-order"),
    path("order-statuses/", views.OrderStatusesList.as_view(), name="order-statuses"),
    path("set-order-status/<str:order_id>", views.set_order_status, name="set-order-status"),
    path(
        "order-report/<str:order_id>/",
        views.get_order_report,
        name="order-report",
    ),
    path(
        "acceptance-report/<str:order_id>/",
        views.get_acceptance_report,
        name="acceptance-report",
    ),
    path(
        "invoice-for-payment/<str:order_id>/",
        views.get_invoice_for_payment,
        name="invoice-for-payment",
    ),
    path("report-defect", views.report_defect, name="report-defect"),
    path("cancel-order", views.cancel_order, name="cancel-order"),
]
