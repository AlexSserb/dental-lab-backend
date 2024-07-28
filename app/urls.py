from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from app.views import index

admin.site.site_header = "InColor Администрирование"
admin.site.site_title = "Администрирование"
admin.site.index_title = "Главная"

urlpatterns = [
    path("", index, name="index"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("accounts/", include("accounts.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
