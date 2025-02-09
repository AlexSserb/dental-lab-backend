from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsLabAdmin
from orders.serializers import ProductTypeSerializer, ProductSerializer, ProductAndOperationsSerializer
from .service import ProductService
from products.models import ProductType


class ProductTypeList(APIView):
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        product_types = ProductType.objects.all().order_by("name")
        serializer = self.serializer_class(product_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(responses=ProductSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, order_id: str):
    return ProductService.get_for_order(order_id)


@extend_schema(responses=ProductAndOperationsSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_products_with_operations(request, order_id):
    """
    View is called once during the formation of the order by the administrator.
    An operation list is generated for each item if it has not been generated previously.
    """
    return ProductService.get_products_with_operations(order_id)
