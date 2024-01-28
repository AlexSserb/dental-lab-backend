from .serializers import *
from .permissions import *

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.views.generic.list import ListView
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


@extend_schema(responses=OrderSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders_for_user(request):
    user = request.user
    orders = Order.objects.filter(user=user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@extend_schema(responses=ProductSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, pk):
    products = Product.objects.filter(order=pk)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@extend_schema(request=ManyProductsFromUserSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    order = Order.objects.create(user=request.user, status=OrderStatus.get_default_status(), discount=0)
    Product.products_from_product_types(request.data['product_types'], order)

    return Response(status=status.HTTP_200_OK)