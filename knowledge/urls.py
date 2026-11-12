from django.urls import path

from . import views

urlpatterns = [
    path("ask/", views.ask_knowledge_base, name="ask-knowledge-base"),
]
