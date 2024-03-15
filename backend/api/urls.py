from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('operation_types/', views.OperationTypeList.as_view(), name='operation-types'),
    path('operation_type/<str:pk>/', views.OperationTypeDetail.as_view(), name='operation-type'),

    path('product_types/', views.ProductTypeList.as_view(), name='product-types'),

    path('orders_for_physician/', views.get_orders_for_physician, name='orders-for-physician'),
    path('orders/', views.get_orders, name='orders'),
    path('processed_orders/', views.get_processed_orders, name='processed-orders'),
    path('not_processed_orders/', views.get_not_processed_orders, name='not-processed-orders'),
    
    path('create_order/', views.create_order, name='create-order'),
    path('products/<str:order_id>/', views.get_products_for_order, name='products-for-order'),

    path('operations_for_tech/', views.get_operations_for_tech, name='operations-for-tech'),
    path('operations_for_product/<str:product_id>', views.get_operations_for_product, name='operations-for-product'),
    path('operation/<str:pk>/', views.OperationDetail.as_view(), name='operation'),
    path('operation_statuses/', views.OperationStatusesList.as_view(), name='operation-statuses'),
]
