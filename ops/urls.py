from django.urls import path

from .views import LangSmithAlertWebhookView

urlpatterns = [
    path("alerts/", LangSmithAlertWebhookView.as_view(), name="langsmith-alert-webhook"),
]
