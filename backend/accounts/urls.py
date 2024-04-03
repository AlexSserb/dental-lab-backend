from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    path('register/', views.register, name='user-registration'),

    path('password-change/', views.changePassword, name='user-password-change'),

    path('profile/<str:email>', views.getUserProfileData, name='user-profile'),
    path('profile/edit-first-name/<str:email>/<str:name>', views.editUserFirstName, name='user-first-name-edit'),
    path('profile/edit-last-name/<str:email>/<str:name>', views.editUserLastName, name='user-last-name-edit'),
]
