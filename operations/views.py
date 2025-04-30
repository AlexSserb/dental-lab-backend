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
    operation_id="get_for_work",
    responses=FullOperationSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="work_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_operations_for_work(request, work_id: str):
    return OperationService.get_for_work(work_id)


@extend_schema(
    operation_id="get_for_tech_schedule",
    responses=OperationForTechScheduleSerializer(many=True),
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
def get_operations_for_tech_schedule(request, date_start: str, tech_email: str):
    return OperationService().get_for_tech_schedule(date_start, tech_email)


@extend_schema(
    operation_id="get_for_schedule",
    responses=OperationForScheduleSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="date_start",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsTech | IsLabAdmin])
def get_operations_for_schedule(request, date_start: str):
    return OperationService().get_for_schedule(date_start)


@extend_schema(
    operation_id="update_operation",
    request=SetOperationDataSerializer,
)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def update_operation(request):
    return OperationService.update_operation(request)


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


@extend_schema(
    operation_id="generate_optimized_plan",
    responses=OperationForScheduleSerializer(many=True),
)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
def generate_optimized_plan(request):
    return OperationService.generate_optimized_plan()


@extend_schema(
    operation_id="apply_optimized_plan",
    request=ApplyOperationsPlanSerializer,
)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
def apply_optimized_plan(request):
    return OperationService.apply_optimized_plan(request)


@extend_schema(
    operation_id="assign_order_operations",
    request=AssignOrderOperations,
)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
def assign_order_operations(request):
    return OperationService.assign_order_operations(request)
