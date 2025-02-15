from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsLabAdmin
from orders.reports import AcceptanceReport, InvoiceForPayment, OrderReport
from core.paginations import *
from .serializers import *
from .service import OrderService

User = get_user_model()


@extend_schema(
    operation_id="get_orders_for_physician",
    responses=OrdersPaginatedListSerializer,
    parameters=[
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders_for_physician(request):
    return OrderService.get_orders_for_physician(request)


@extend_schema(
    operation_id="get_order",
    responses=OrderWithPhysicianSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="year",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="month",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_orders(request, year: int, month: int):
    return OrderService.get_orders_for_month(year, month)


@extend_schema(
    operation_id="create_order",
    request=DataForOrderCreationSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    return OrderService.create_order(request)


@extend_schema(
    operation_id="confirm_order",
    request=OrderDiscountSetterSerializer,
    responses=OrderSerializer,
)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
def confirm_order(request):
    return OrderService.confirm_order(request)


@extend_schema(
    operation_id="set_order_status",
    request=UpdateOrderStatusSerializer,
    responses=OrderWithPhysicianSerializer,
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def set_order_status(request, order_id: str):
    return OrderService.set_order_status(request, order_id)


@extend_schema(operation_id="get_order_statuses")
class OrderStatusesList(ListAPIView):
    queryset = OrderStatus.objects.order_by("number").all()
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order_report(request, order_id: str):
    return OrderService.get_order(order_id, OrderReport)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_acceptance_report(request, order_id: str):
    return OrderService.get_order(order_id, AcceptanceReport)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoice_for_payment(request, order_id: str):
    return OrderService.get_order(order_id, InvoiceForPayment)
