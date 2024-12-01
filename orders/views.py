from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import *
from rest_framework.views import APIView

from accounts.permissions import *
from .paginations import *
from .serializers import *
from .services import OperationService, OrderService, ProductService

User = get_user_model()


class OperationTypeList(APIView):
    serializer_class = OperationTypeSerializer
    permission_classes = [IsDirector | IsLabAdmin | IsChiefTech | IsTech]

    def get(self, request, *args, **kwargs):
        operation_types = OperationType.objects.all()
        serializer = self.serializer_class(operation_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OperationTypeDetail(APIView):
    """
    Retrieve, update or delete an operation type instance.
    """

    permission_classes = [IsDirector | IsLabAdmin | IsChiefTech]
    serializer_class = OperationTypeSerializer

    def get_object(self, pk):
        try:
            return OperationType.objects.get(pk=pk)
        except OperationType.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type)
        return Response(serializer.data)

    def put(self, request, pk):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        oper_type = self.get_object(pk)
        oper_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductTypeList(APIView):
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        product_types = ProductType.objects.all().order_by("name")
        serializer = self.serializer_class(product_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(responses=OrderSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders_for_physician(request):
    return OrderService.get_orders_for_physician(request)


@extend_schema(responses=OrderWithPhysicianSerializer)
@api_view(["GET"])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_orders(request, year: int, month: int):
    return OrderService.get_orders_for_month(year, month)


@extend_schema(responses=ProductSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, order_id: str):
    return ProductService.get_for_order(order_id)


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
@permission_classes([IsLabAdmin | IsDirector])
def confirm_order(request):
    serializer = OrderDiscountSetterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            return OrderService.confirm_order(serializer)

        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=OperationSerializer)
@api_view(["GET"])
@permission_classes([IsTech | IsChiefTech])
def get_operations_for_tech(request):
    return OperationService.get_for_tech(request)


@extend_schema(responses=OperationForProductSerializer)
@api_view(["GET"])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_operations_for_product(request, product_id):
    return OperationService.get_for_product(product_id)


@extend_schema(responses=OperationForScheduleSerializer)
@api_view(["GET"])
@permission_classes([IsTech | IsChiefTech | IsLabAdmin | IsDirector])
def get_operations_for_schedule(request, user_email: str, date: str):
    operation_service = OperationService()
    return operation_service.get_for_schedule(user_email, date)


@extend_schema()
@api_view(["PATCH"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def set_operation_exec_start(request, id: str, exec_start: str):
    return OperationService.set_execution_start(id, exec_start)


@extend_schema(request=UpdateOrderStatusSerializer, responses=OrderWithPhysicianSerializer)
@api_view(["PATCH"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def set_order_status(request, id: str):
    order = get_object_or_404(Order, id=id)
    serializer = UpdateOrderStatusSerializer(data=request.data)
    if serializer.is_valid():
        return OrderService.set_order_status(serializer, order)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=AssignOperationSerializer)
@api_view(["PATCH"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def assign_operation(request):
    serializer = AssignOperationSerializer(data=request.data)
    if serializer.is_valid():
        return OperationService.assign(serializer)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperationDetail(APIView):
    """
    Retrieve, update or delete an operation instance.
    """

    permission_classes = [IsTech | IsChiefTech]
    serializer_class = OperationSerializer

    def get_object(self, pk):
        try:
            return Operation.objects.get(pk=pk)
        except Operation.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        operation = self.get_object(pk)
        serializer = self.serializer_class(operation)
        return Response(serializer.data)

    @extend_schema(request=UpdateOperationStatusSerializer)
    def patch(self, request, pk, format=None):
        """
        Allows only the status of an operation to be changed via the status field
        """
        serializer = UpdateOperationStatusSerializer(data=request.data)
        if serializer.is_valid():
            operation = get_object_or_404(Operation, id=pk)
            operation.operation_status = serializer.validated_data["status"]
            operation.save()
            return Response(self.serializer_class(operation).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        operation = self.get_object(pk)
        operation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperationStatusesList(ListAPIView):
    queryset = OperationStatus.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OperationStatusSerializer


class OrderStatusesList(ListAPIView):
    queryset = OrderStatus.objects.order_by("number").all()
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusSerializer


@extend_schema(responses=ProductAndOperationsSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def get_products_with_operations(request, order_id):
    """
    View is called once during the formation of the order by the administrator.
    An operation list is generated for each item if it has not been generated previously.
    """
    return ProductService.get_products_with_operations(order_id)
