from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('register/', views.register, name='user-registration'),

    path('profile/', views.getUserProfileData, name='user-profile'),
    path('operation_types/', views.OperationTypeList.as_view(), name='operation-types'),
    path('operation_types/<str:pk>/', views.OperationTypeDetail.as_view(), name='operation-type'),
    path('orders/', views.getOrdersForUser, name='orders-for-user'),
    path('products/<str:pk>/', views.getProductsForOrder, name='products-for-order')
]
