from django.urls import path

from . import views

urlpatterns = [
    path("product-types/", views.ProductTypeList.as_view(), name="product-types"),
    path("<str:order_id>/", views.get_products_for_order, name="products-for-order"),
    path("operations/<str:order_id>", views.get_products_with_operations,
         name="products-with-operations"),
]
