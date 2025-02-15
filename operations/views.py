from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsLabAdmin, IsTech
from operations.serializers import *
from .service import OperationService


@extend_schema(
    operation_id="get_for_tech",
    responses=OperationsPaginatedListSerializer,
    parameters=[
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsTech])
def get_operations_for_tech(request):
    return OperationService.get_for_tech(request)


@extend_schema(
    operation_id="get_for_product",
    responses=FullOperationSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="product_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_operations_for_product(request, product_id: str):
    return OperationService.get_for_product(product_id)


@extend_schema(
    operation_id="get_for_schedule",
    responses=OperationForScheduleSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="date_start",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="tech_email",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsTech | IsLabAdmin])
def get_operations_for_schedule(request, date_start: str, tech_email: str):
    return OperationService().get_for_schedule(date_start, tech_email)


@extend_schema(
    operation_id="set_operation_exec_start",
    parameters=[
        OpenApiParameter(
            name="operation_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="exec_start",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def set_operation_exec_start(request, operation_id: str, exec_start: str):
    return OperationService.set_execution_start(operation_id, exec_start)


@extend_schema(
    operation_id="assign_operation",
    request=AssignOperationSerializer,
)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def assign_operation(request):
    return OperationService.assign(request)


@extend_schema(
    operation_id="update_operation_status",
    request=UpdateOperationStatusSerializer,
    responses=OperationSerializer,
    parameters=[
        OpenApiParameter(
            name="operation_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin | IsTech])
def update_operation_status(request, operation_id: str):
    return OperationService.update_status(request, operation_id)


@extend_schema(operation_id="get_operation_statuses")
class OperationStatusesList(ListAPIView):
    queryset = OperationStatus.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OperationStatusSerializer
