from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsLabAdmin
from works.models import WorkType
from .serializers import WorkTypeSerializer, WorkSerializer, WorkAndOperationsSerializer
from .service import WorkService


@extend_schema(operation_id="get_work_types")
class WorkTypeList(ListAPIView):
    queryset = WorkType.objects.order_by("name").all()
    serializer_class = WorkTypeSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    operation_id="get_for_order",
    responses=WorkSerializer(many=True),
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
def get_works_for_order(request, order_id: str):
    return WorkService.get_for_order(order_id)


@extend_schema(
    operation_id="get_with_operations",
    responses=WorkAndOperationsSerializer(many=True),
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
def get_works_with_operations(request, order_id: str):
    """
    View is called once during the formation of the order by the administrator.
    An operation list is generated for each item if it has not been generated previously.
    """
    return WorkService.get_works_with_operations(order_id)
