from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsLabAdmin
from products.models import ProductType
from .serializers import ProductTypeSerializer, ProductSerializer, ProductAndOperationsSerializer
from .service import ProductService


@extend_schema(operation_id="get_product_types")
class ProductTypeList(ListAPIView):
    queryset = ProductType.objects.order_by("name").all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    operation_id="get_for_order",
    responses=ProductSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products_for_order(request, order_id: str):
    return ProductService.get_for_order(order_id)


@extend_schema(
    operation_id="get_with_operations",
    responses=ProductAndOperationsSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_products_with_operations(request, order_id: str):
    """
    View is called once during the formation of the order by the administrator.
    An operation list is generated for each item if it has not been generated previously.
    """
    return ProductService.get_products_with_operations(order_id)
