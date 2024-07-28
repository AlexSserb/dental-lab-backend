from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    path('register/', views.register, name='user-registration'),

    path('password-change/', views.change_password, name='user-password-change'),

    path('profile/<str:email>', views.get_user_profile_data, name='user-profile'),
    path('profile/edit-first-name/<str:email>/<str:name>', views.edit_user_first_name, name='user-first-name-edit'),
    path('profile/edit-last-name/<str:email>/<str:name>', views.edit_user_last_name, name='user-last-name-edit'),

    path('technicians/<int:group_id>', views.get_technicians_by_group, name='technicians-by-group'),
]
