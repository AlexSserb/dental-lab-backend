from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from app import views

admin.site.site_header = "InColor Администрирование"
admin.site.site_title = "Администрирование"
admin.site.index_title = "Главная"

urlpatterns = [
    path("api/", include([
        path("orders/", include("orders.urls")),
        path("accounts/", include("accounts.urls")),
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    ])),
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
]
