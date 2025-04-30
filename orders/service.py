import calendar
from datetime import datetime, timedelta
from typing import Type

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
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
    UpdateOrderStatusSerializer, ReportDefectSerializer, CancelOrderSerializer,
)
from works.models import Work, WorkStatus


class OrderService:
    @staticmethod
    def get_orders_for_physician(request: WSGIRequest) -> Response:
        order_status_cancelled = OrderStatus.get_canceled_status()
        user = request.user
        paginator = StandardResultsSetPagination()
        orders = Order.objects.filter(~Q(status_id=order_status_cancelled.id), user=user).order_by("-order_date")
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @staticmethod
    def get_orders_for_month(year: int, month: int) -> Response:
        order_status_cancelled = OrderStatus.get_canceled_status()
        date_from = datetime(year=year, month=month, day=1)
        date_to = datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
        orders = Order.objects.filter(
            ~Q(status_id=order_status_cancelled.id),
            is_active=True,
            order_date__range=(date_from, date_to),
        ).order_by("-order_date")
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
        Work.works_from_work_types(request.data["work_types"], order)

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

            for work_validated in serializer.validated_data["works_discounts_data"]:
                work = Work.objects.get(pk=work_validated["id"])
                work.discount = work_validated["discount"]
                work.save()

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

    @staticmethod
    def report_defect(request) -> Response:
        serializer = ReportDefectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.validated_data["order"]
        order.comment_after_accept = serializer.validated_data["comment_after_accept"]
        order.status = OrderStatus.get_defect_status()
        order.save()

        for work in serializer.validated_data["works"]:
            work.work_status = WorkStatus.get_defect_status()
            work.save()

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def cancel_order(request) -> Response:
        serializer = CancelOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.validated_data["order"]
        order.status = OrderStatus.get_canceled_status()
        order.save()

        return Response(status=status.HTTP_200_OK)
