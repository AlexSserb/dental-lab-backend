from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from accounts.models import User
from core.paginations import StandardResultsSetPagination
from operations.serializers import *
from products.models import Product


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
        serializer = FullOperationSerializer(operations, many=True)

        # get history of operations for a product
        all_operations_history = OperationEvent.objects.select_related("operation_status")
        for operation in serializer.data:
            curr_history = all_operations_history.filter(pgh_obj=operation["id"]).order_by("-pgh_created_at")
            operation["history"] = OperationEventSerializer(curr_history, many=True).data

        return Response(serializer.data)

    @staticmethod
    def _preprocess_operation_for_schedule(operation: Operation, with_tech: bool = False) -> dict[
        str, UUID | datetime | OperationType | OperationStatus | Product | list
    ]:
        processed = {}
        exec_time = operation.operation_type.exec_time
        delta = timedelta(hours=exec_time.hour, minutes=exec_time.minute, seconds=exec_time.second)

        processed["id"] = operation.id
        processed["start"] = operation.exec_start
        processed["end"] = operation.exec_start + delta
        processed["operation_type"] = operation.operation_type
        processed["operation_status"] = operation.operation_status
        processed["product"] = operation.product
        processed["editable"] = operation.is_exec_start_editable
        processed["deadline"] = operation.product.order.deadline
        if with_tech:
            processed["resource_id"] = operation.tech.email
            processed["group_id"] = operation.operation_type.group
            processed["error"] = False
            processed["error_description"] = ""

        return processed

    @staticmethod
    def _group_operations_by_product(operations: list[dict]) -> list[dict]:
        operations_order_error = "Порядок операций нарушен"
        deadline_error = "Срок выполнения заказа нарушен"
        no_pause_error = "Между операциями должен быть перерыв 10+ минут"

        operations_dict = {}
        product_operations: dict[int, list[dict]] = defaultdict(list)

        for operation in operations:
            operations_dict[operation["id"]] = operation
            product_operations[operation["product"].id].append(operation)

        for product, operations in product_operations.items():
            for i in range(1, len(operations)):
                if operations[i - 1]["end"] >= operations[i]["start"]:
                    operations[i - 1]["error"] = True
                    operations[i - 1]["error_description"] = operations_order_error
                    operations[i]["error"] = True
                    operations[i]["error_description"] = operations_order_error
                elif operations[i]["end"].date() > operations[i]["deadline"]:
                    operations[i]["error"] = True
                    operations[i]["error_description"] = deadline_error

            sorted_operations = sorted(operations, key=lambda op: op["start"])
            for i in range(1, len(sorted_operations)):
                if operations[i - 1]["end"] - sorted_operations[i - 1]["start"] > timedelta(minutes=10):
                    operations[i - 1]["error"] = True
                    operations[i - 1]["error_description"] = no_pause_error
                    operations[i]["error"] = True
                    operations[i]["error_description"] = no_pause_error

        operations = []
        for operations_row in product_operations.values():
            operations += operations_row

        return operations

    def get_for_tech_schedule(self, date: str, user_email: str) -> Response:
        date_start = datetime.strptime(date, "%d.%m.%Y").date()
        date_end = date_start + timedelta(days=5)
        user = User.objects.filter(email=user_email).first()
        operations = (
            Operation.objects
            .filter(tech=user, exec_start__gte=str(date_start), exec_start__lte=str(date_end))
        )
        operations = [
            self._preprocess_operation_for_schedule(operation) for operation in operations
        ]
        serializer = OperationForTechScheduleSerializer(operations, many=True)
        return Response(serializer.data)

    def get_for_schedule(self, date: str) -> Response:
        date_start = datetime.strptime(date, "%d.%m.%Y").date() - timedelta(days=1)
        date_end = date_start + timedelta(days=15)
        operations = (
            Operation.objects
            .filter(exec_start__gte=str(date_start), exec_start__lte=str(date_end))
            .order_by("ordinal_number")
        )
        operations = [
            self._preprocess_operation_for_schedule(operation, with_tech=True) for operation in operations
        ]
        operations = self._group_operations_by_product(operations)
        serializer = OperationForScheduleSerializer(operations, many=True)
        return Response(serializer.data)

    @staticmethod
    def update_operation(request: SetOperationDataSerializer) -> Response:
        operation = get_object_or_404(Operation, id=request.data["operation_id"])
        if "exec_start" in request.data:
            operation.exec_start = datetime.strptime(request.data["exec_start"], "%a, %d %b %Y %H:%M:%S %Z")
        if "tech_email" in request.data:
            tech = get_object_or_404(User, email=request.data["tech_email"])
            operation.tech = tech
        if "editable" in request.data:
            operation.is_exec_start_editable = request.data["editable"]

        operation.save()

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def assign(request) -> Response:
        serializer = AssignOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        operation = get_object_or_404(Operation, id=serializer.validated_data["id"])
        operation.tech = get_object_or_404(User, email=serializer.validated_data["tech_email"])
        operation.exec_start = datetime.strptime(serializer.validated_data["exec_start"], "%d.%m.%Y %H:%M")
        operation.save()
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def update_status(request, operation_id: str) -> Response:
        serializer = UpdateOperationStatusSerializer(data=request.data)
        if serializer.is_valid():
            operation = get_object_or_404(Operation, id=operation_id)
            operation.operation_status = serializer.validated_data["status"]
            operation.save()
            return Response(OperationSerializer(operation).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
