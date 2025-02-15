from django.urls import path

from . import views

urlpatterns = [
    path("token/", views.CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", views.CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("register/", views.register, name="user-registration"),
    path("send-email-verification/", views.send_email_verification, name="send-email-verification"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path("password-change/", views.change_password, name="user-password-change"),
    path("profile/<str:email>", views.get_user_profile_data, name="user-profile"),
    path(
        "profile/edit-first-name/<str:email>/<str:name>",
        views.edit_user_first_name,
        name="user-first-name-edit",
    ),
    path(
        "profile/edit-last-name/<str:email>/<str:name>",
        views.edit_user_last_name,
        name="user-last-name-edit",
    ),
    path(
        "technicians/<int:group_id>",
        views.get_technicians_by_group,
        name="technicians-by-group",
    ),
    path("customers/", views.get_customers, name="get-all-customers"),
    path(
        "customers/attach",
        views.attach_customers_to_user,
        name="attach-customers-to-users",
    ),
]
