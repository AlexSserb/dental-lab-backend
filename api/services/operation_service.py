from datetime import datetime, timedelta

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from accounts.models import User
from api.models import Operation, OperationEvent
from api.paginations import StandardResultsSetPagination
from api.serializers import (
    OperationSerializer,
    OperationForProductSerializer,
    OperationEventSerializer,
    OperationForScheduleSerializer,
    AssignOperationSerializer,
)


class OperationService:
    @staticmethod
    def get_for_tech(request: WSGIRequest) -> Response:
        user = request.user
        paginator = StandardResultsSetPagination()
        operations = Operation.objects.filter(tech=user).order_by("id")
        page = paginator.paginate_queryset(operations, request)
        serializer = OperationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @staticmethod
    def get_for_product(product_id: str) -> Response:
        operations = Operation.objects.filter(product=product_id).order_by("operation_status__number")
        serializer = OperationForProductSerializer(operations, many=True)

        # get history of operations for a product
        all_operations_history = OperationEvent.objects.select_related("operation_status")
        for operation in serializer.data:
            curr_history = all_operations_history.filter(pgh_obj=operation["id"]).order_by("-pgh_created_at")
            operation["history"] = OperationEventSerializer(curr_history, many=True).data

        return Response(serializer.data)

    @staticmethod
    def _preprocess_operation_for_schedule(operation) -> dict[str, timedelta]:
        processed = {}
        exec_time = operation.operation_type.exec_time
        delta = timedelta(hours=exec_time.hour, minutes=exec_time.minute, seconds=exec_time.second)

        processed["id"] = operation.id
        processed["start"] = operation.exec_start
        processed["end"] = operation.exec_start + delta
        processed["operation_type"] = operation.operation_type
        processed["operation_status"] = operation.operation_status
        processed["product"] = operation.product

        return processed

    def get_for_schedule(self, user_email: str, date: str) -> Response:
        date_start = datetime.strptime(date, "%Y-%m-%d").date()
        date_end = date_start + timedelta(days=5)
        user = User.objects.filter(email=user_email).first()
        operations = Operation.objects.filter(tech=user, exec_start__gte=str(date_start), exec_start__lte=str(date_end))
        operations = [self._preprocess_operation_for_schedule(operation) for operation in operations]
        serializer = OperationForScheduleSerializer(operations, many=True)
        return Response(serializer.data)

    @staticmethod
    def set_execution_start(operation_id: str, exec_start: str) -> Response:
        operation = get_object_or_404(Operation, id=operation_id)
        operation.exec_start = datetime.strptime(exec_start, "%a, %d %b %Y %H:%M:%S %Z")
        operation.save()

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def assign(serializer: AssignOperationSerializer) -> Response:
        operation = get_object_or_404(Operation, id=serializer.validated_data["id"])
        operation.tech = get_object_or_404(User, email=serializer.validated_data["tech_email"])
        operation.exec_start = datetime.strptime(serializer.validated_data["exec_start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        operation.save()
        return Response(status=status.HTTP_200_OK)
