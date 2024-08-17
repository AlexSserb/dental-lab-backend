from .serializers import *
from accounts.permissions import *
from .paginations import *

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from django.db.models import Q
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import *
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from datetime import datetime, timedelta
import calendar
import pytz


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

    def get(self, request, pk, format=None):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
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
    user = request.user
    paginator = StandardResultsSetPagination()
    orders = Order.objects.filter(user=user).order_by("-order_date")
    page = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(responses=OrderWithPhysicianSerializer)
@api_view(["GET"])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_orders(request, year: int, month: int):
    date_from = datetime(year=year, month=month, day=1)
    date_to = datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
    orders = Order.objects.filter(
        is_active=True, order_date__range=(date_from, date_to)
    ).order_by("-order_date")
    serializer = OrderWithPhysicianSerializer(orders, many=True)
    return Response(serializer.data)


@extend_schema(responses=ProductSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, order_id):
    products = Product.objects.filter(order=order_id)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@extend_schema(request=DataForOrderCreationSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    serializer = DataForOrderCreationSerializer(data=request.data)
    if serializer.is_valid():
        order = Order.objects.create(
            user=request.user,
            status=OrderStatus.get_default_status(),
            discount=0,
            customer=serializer.validated_data["customer_id"],
        )
        Product.products_from_product_types(request.data["product_types"], order)
        return Response(status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OrderDiscountSetterSerializer, responses=OrderSerializer)
@api_view(["POST"])
@permission_classes([IsLabAdmin | IsDirector])
def confirm_order(request):
    serializer = OrderDiscountSetterSerializer(data=request.data)
    if serializer.is_valid():
        try:
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

        except Exception as ex:
            return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=OperationSerializer)
@api_view(["GET"])
@permission_classes([IsTech | IsChiefTech])
def get_operations_for_tech(request):
    user = request.user
    paginator = StandardResultsSetPagination()
    operations = Operation.objects.filter(tech=user).order_by("id")
    page = paginator.paginate_queryset(operations, request)
    serializer = OperationSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(responses=OperationForProductSerializer)
@api_view(["GET"])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_operations_for_product(request, product_id):
    operations = Operation.objects.filter(product=product_id).order_by(
        "operation_status__number"
    )
    serializer = OperationForProductSerializer(operations, many=True)

    # get history of operations for a product
    all_operations_history = OperationEvent.objects.select_related("operation_status")
    for operation in serializer.data:
        curr_history = all_operations_history.filter(pgh_obj=operation["id"]).order_by(
            "-pgh_created_at"
        )
        operation["history"] = OperationEventSerializer(curr_history, many=True).data

    return Response(serializer.data)


def preprocess_operation_for_schedule(operation):
    processed = {}
    exec_time = operation.operation_type.exec_time
    delta = timedelta(
        hours=exec_time.hour, minutes=exec_time.minute, seconds=exec_time.second
    )

    processed["id"] = operation.id
    processed["start"] = operation.exec_start
    processed["end"] = operation.exec_start + delta
    processed["operation_type"] = operation.operation_type
    processed["operation_status"] = operation.operation_status
    processed["product"] = operation.product

    return processed


@extend_schema(responses=OperationForScheduleSerializer)
@api_view(["GET"])
@permission_classes([IsTech | IsChiefTech | IsLabAdmin | IsDirector])
def get_operations_for_schedule(request, user_email, date):
    date_start = datetime.strptime(date, "%Y-%m-%d").date()
    date_end = date_start + timedelta(days=5)
    user = User.objects.filter(email=user_email).first()
    operations = Operation.objects.filter(
        tech=user, exec_start__gte=str(date_start), exec_start__lte=str(date_end)
    )
    operations = [
        preprocess_operation_for_schedule(operation) for operation in operations
    ]
    serializer = OperationForScheduleSerializer(operations, many=True)
    return Response(serializer.data)


@extend_schema()
@api_view(["PATCH"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def set_operation_exec_start(request, id, exec_start):
    operation = get_object_or_404(Operation, id=id)
    operation.exec_start = datetime.strptime(exec_start, "%a, %d %b %Y %H:%M:%S %Z")
    operation.save()

    return Response(status=status.HTTP_200_OK)


@extend_schema(request=AssignOperationSerializer)
@api_view(["PATCH"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def assign_operation(request):
    serializer = AssignOperationSerializer(data=request.data)
    if serializer.is_valid():
        operation = get_object_or_404(Operation, id=serializer.validated_data["id"])
        operation.tech = get_object_or_404(
            User, email=serializer.validated_data["tech_email"]
        )
        operation.exec_start = datetime.strptime(
            serializer.validated_data["exec_start"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        operation.save()
        return Response(status=status.HTTP_200_OK)

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
        Allows only the status of an operation to be changed via the status_id field
        """
        serializer = UpdateOperationStatusSerializer(data=request.data)
        if serializer.is_valid():
            operation = Operation.objects.filter(id=pk).first()
            operation_status = OperationStatus.objects.filter(
                id=serializer.validated_data["status_id"]
            ).first()
            if not operation or not operation_status:
                return Response(status=status.HTTP_404_NOT_FOUND)
            operation.operation_status = operation_status
            operation.save()
            return Response(self.serializer_class(operation).data)
        return Response(serializer.errors)

    def delete(self, request, pk, format=None):
        operation = self.get_object(pk)
        operation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperationStatusesList(ListAPIView):
    queryset = OperationStatus.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OperationStatusSerializer


@extend_schema(responses=ProductAndOperationsSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def get_products_with_operations(request, order_id):
    """
    View is called once during the formation of the order by the administrator.
    An operation list is generated for each item if it has not been generated previously.
    """
    try:
        order = Order.objects.get(id=order_id)
        for product in order.products.all():
            if product.operations.count() == 0:
                for operation_type, through in zip(
                    product.product_type.operation_types.all(),
                    product.product_type.operation_types.through.objects.all(),
                ):
                    Operation.objects.create(
                        product=product,
                        operation_type=operation_type,
                        operation_status=OperationStatus.get_default_status(),
                        ordinal_number=through.ordinal_number,
                    )

        serializer = ProductAndOperationsSerializer(order.products, many=True)
        return Response(serializer.data)
    except Order.DoesNotExist:
        raise Http404
