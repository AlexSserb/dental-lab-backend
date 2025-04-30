from django.urls import path

from . import views

urlpatterns = [
    path("work-types/", views.WorkTypeList.as_view(), name="work-types"),
    path("<str:order_id>/", views.get_works_for_order, name="work-for-order"),
    path("operations/<str:order_id>", views.get_works_with_operations,
         name="works-with-operations"),
]
