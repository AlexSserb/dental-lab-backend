import calendar
from datetime import datetime

from django.core.handlers.wsgi import WSGIRequest
from rest_framework import status
from rest_framework.response import Response

from api.models import Order, OrderStatus, Product, ProductStatus
from api.paginations import StandardResultsSetPagination
from api.serializers import (
    OrderSerializer,
    OrderWithPhysicianSerializer,
    DataForOrderCreationSerializer,
    OrderDiscountSetterSerializer,
    UpdateOrderStatusSerializer,
)


class OrderService:
    @staticmethod
    def get_orders_for_physician(request: WSGIRequest) -> Response:
        user = request.user
        paginator = StandardResultsSetPagination()
        orders = Order.objects.filter(user=user).order_by("-order_date")
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @staticmethod
    def get_orders_for_month(year: int, month: int) -> Response:
        date_from = datetime(year=year, month=month, day=1)
        date_to = datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
        orders = Order.objects.filter(is_active=True, order_date__range=(date_from, date_to)).order_by("-order_date")
        serializer = OrderWithPhysicianSerializer(orders, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_order(request: WSGIRequest, serializer: DataForOrderCreationSerializer) -> None:
        order = Order.objects.create(
            user=request.user,
            status=OrderStatus.get_default_status(),
            discount=0,
            customer=serializer.validated_data["customer_id"],
        )
        Product.products_from_product_types(request.data["product_types"], order)

    @staticmethod
    def confirm_order(serializer: OrderDiscountSetterSerializer) -> Response:
        order = Order.objects.get(pk=serializer.validated_data["order"]["id"])
        order.discount = serializer.validated_data["order"]["discount"]
        order.status = OrderStatus.objects.get(number=2)
        order.save()

        product_status = ProductStatus.objects.get(number=2)
        for product_validated in serializer.validated_data["products"]:
            product = Product.objects.get(pk=product_validated["id"])
            product.discount = product_validated["discount"]
            product.product_status = product_status
            product.save()

        order_serializer = OrderWithPhysicianSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def set_order_status(serializer: UpdateOrderStatusSerializer, order: Order) -> Response:
        order.status = serializer.validated_data["status"]
        order.save()
        order_serializer = OrderWithPhysicianSerializer(order)
        return Response(order_serializer.data)
