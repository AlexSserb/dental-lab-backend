from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('operation_types/', views.OperationTypeList.as_view(), name='operation-types'),
    path('operation_types/<str:pk>/', views.OperationTypeDetail.as_view(), name='operation-type'),
    path('orders/', views.getOrdersForUser, name='orders-for-user'),
    path('products/<str:pk>/', views.getProductsForOrder, name='products-for-order')
]
