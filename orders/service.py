import calendar
import json
from datetime import datetime, timedelta
from typing import Type

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from accounts.models import DentalLabData
from core.paginations import StandardResultsSetPagination
from orders.models import Order, OrderStatus
from orders.reports import Report
from orders.serializers import (
    OrderSerializer,
    OrderWithPhysicianSerializer,
    DataForOrderCreationSerializer,
    OrderDiscountSetterSerializer,
    UpdateOrderStatusSerializer,
)
from products.models import Product


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
    def create_order(request) -> Response:
        serializer = DataForOrderCreationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            user=request.user,
            status=OrderStatus.get_default_status(),
            discount=0,
            customer=serializer.validated_data["customer_id"],
            comment=serializer.validated_data["comment"],
            deadline=datetime.now() + timedelta(days=5),
        )
        Product.products_from_product_types(request.data["product_types"], order)

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def confirm_order(request) -> Response:
        serializer = OrderDiscountSetterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(pk=serializer.validated_data["order_discount_data"]["id"])
            order.discount = serializer.validated_data["order_discount_data"]["discount"]
            order.status = OrderStatus.objects.get(number=2)
            order.save()

            for product_validated in serializer.validated_data["products_discounts_data"]:
                product = Product.objects.get(pk=product_validated["id"])
                product.discount = product_validated["discount"]
                product.save()

            order_serializer = OrderWithPhysicianSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def set_order_status(request, order_id) -> Response:
        order = get_object_or_404(Order, id=order_id)
        serializer = UpdateOrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order.status = serializer.validated_data["status"]
        order.save()
        order_serializer = OrderWithPhysicianSerializer(order)
        return Response(order_serializer.data)

    @staticmethod
    def get_order(order_id: str, report_class: Type[Report]):
        order = Order.objects.get(id=order_id)
        dental_lab_data = DentalLabData.objects.get()
        report = report_class(order, dental_lab_data)
        response = HttpResponse(bytes(report.output()), content_type="application/pdf")
        return response
