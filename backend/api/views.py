from .serializers import *
from .permissions import *
from .paginations import *

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import *
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema


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
        product_types = ProductType.objects.all().order_by('name')
        serializer = self.serializer_class(product_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(responses=OrderSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders_for_physician(request):
    user = request.user
    paginator = StandardResultsSetPagination()
    orders = Order.objects.filter(user=user).order_by('-order_date')
    page = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(responses=OrderSerializer)
@api_view(['GET'])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_orders(request):
    paginator = StandardResultsSetPagination()
    orders = Order.objects.all().order_by('-order_date')
    page = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(responses=ProductSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, order_id):
    products = Product.objects.filter(order=order_id)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@extend_schema(request=ManyProductsFromUserSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    serializer = ManyProductsFromUserSerializer(data=request.data)
    if serializer.is_valid():
        order = Order.objects.create(user=request.user, status=OrderStatus.get_default_status(), discount=0)
        Product.products_from_product_types(request.data['product_types'], order)
        return Response(status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=OperationSerializer)
@api_view(['GET'])
@permission_classes([IsTech | IsChiefTech])
def get_operations_for_tech(request):
    user = request.user
    paginator = StandardResultsSetPagination()
    operations = Operation.objects.filter(tech=user).order_by('id')
    page = paginator.paginate_queryset(operations, request)
    serializer = OperationSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(responses=OperationForProductSerializer)
@api_view(['GET'])
@permission_classes([IsDirector | IsLabAdmin | IsChiefTech])
def get_operations_for_product(request, product_id):
    operations = Operation.objects.filter(product=product_id).order_by('operation_status__number')
    serializer = OperationForProductSerializer(operations, many=True)

    # get history of operations for a product
    all_operations_history = OperationEvent.objects.select_related('operation_status')
    for operation in serializer.data:
        curr_history = all_operations_history.filter(pgh_obj=operation['id']).order_by('-pgh_created_at')
        operation['history'] = OperationEventSerializer(curr_history, many=True).data
        
    return Response(serializer.data)


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
            operation_status = OperationStatus.objects.filter(id=serializer.validated_data['status_id']).first()
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
