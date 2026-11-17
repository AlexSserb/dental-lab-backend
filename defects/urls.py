from django.urls import path

from . import views

urlpatterns = [
    path("triage/", views.triage_list, name="defect-triage-list"),
    path("triage/<uuid:triage_id>/", views.triage_detail, name="defect-triage-detail"),
    path("triage/<uuid:triage_id>/decision", views.triage_decision, name="defect-triage-decision"),
]
