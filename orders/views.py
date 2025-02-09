from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import *

from accounts.permissions import IsLabAdmin
from core.paginations import *
from .serializers import *
from .service import OrderService

User = get_user_model()


@extend_schema(responses=OrderSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders_for_physician(request):
    return OrderService.get_orders_for_physician(request)


@extend_schema(responses=OrderWithPhysicianSerializer)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_orders(request, year: int, month: int):
    return OrderService.get_orders_for_month(year, month)


@extend_schema(request=DataForOrderCreationSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    serializer = DataForOrderCreationSerializer(data=request.data)
    if serializer.is_valid():
        OrderService.create_order(request, serializer)
        return Response(status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OrderDiscountSetterSerializer, responses=OrderSerializer)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
def confirm_order(request):
    serializer = OrderDiscountSetterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            return OrderService.confirm_order(serializer)

        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=UpdateOrderStatusSerializer, responses=OrderWithPhysicianSerializer)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def set_order_status(request, id: str):
    order = get_object_or_404(Order, id=id)
    serializer = UpdateOrderStatusSerializer(data=request.data)
    if serializer.is_valid():
        return OrderService.set_order_status(serializer, order)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderStatusesList(ListAPIView):
    queryset = OrderStatus.objects.order_by("number").all()
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusSerializer
