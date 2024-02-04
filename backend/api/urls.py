from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('operation_types/', views.OperationTypeList.as_view(), name='operation-types'),
    path('operation_types/<str:pk>/', views.OperationTypeDetail.as_view(), name='operation-type'),

    path('product_types/', views.ProductTypeList.as_view(), name='product-types'),

    path('orders/', views.get_orders_for_user, name='orders-for-user'),
    path('create_order/', views.create_order, name='create-order'),
    path('products/<str:pk>/', views.get_products_for_order, name='products-for-order'),

    path('operations_for_tech/', views.get_operations_for_tech, name='operations-for-tech'),
]
