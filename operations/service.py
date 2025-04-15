import heapq
from collections import defaultdict
from datetime import datetime, timedelta, date, time
from uuid import UUID

import pytz
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from accounts.models import User
from accounts.services.user_service import UserService
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
            processed["resource_id"] = operation.tech.email if operation.tech else None
            processed["group_id"] = operation.operation_type.group
            processed["error"] = False
            processed["error_description"] = ""

        return processed

    @staticmethod
    def _group_operations_by_product(operations: list[dict]) -> list[dict]:
        operations_order_error = "Порядок операций нарушен"
        deadline_error = "Срок выполнения заказа нарушен"
        no_pause_error = "Между операциями должен быть перерыв 5+ минут"

        product_operations: dict[int, list[dict]] = defaultdict(list)
        tech_operations: dict[int, list[dict]] = defaultdict(list)

        for operation in operations:
            product_operations[operation["product"].id].append(operation)
            tech_operations[operation["resource_id"]].append(operation)

        for tech_email, operations in tech_operations.items():
            sorted_operations = sorted(operations, key=lambda op: op["start"])

            for i in range(1, len(sorted_operations)):
                if sorted_operations[i]["start"] - sorted_operations[i - 1]["end"] < timedelta(minutes=5):
                    sorted_operations[i - 1]["error"] = True
                    sorted_operations[i - 1]["error_description"] = no_pause_error
                    sorted_operations[i]["error"] = True
                    sorted_operations[i]["error_description"] = no_pause_error

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

    @staticmethod
    def _get_operations_to_distribute():
        operations = (
            Operation.objects
            .select_related(
                'product__order'
            ).order_by(
                'product__order__deadline',
                'product_id',
                'ordinal_number'
            )
        )
        return operations

    @staticmethod
    def _adjust_to_work_hours(start_time: datetime, duration: timedelta) -> tuple[datetime, datetime]:
        """
        Adjusts operation time to fit within work hours (8:00-19:00).
        Returns tuple of (adjusted_start_time, adjusted_end_time)
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=pytz.UTC)

        workday_start = time(4, 0, tzinfo=pytz.UTC)
        workday_end = time(15, 0, tzinfo=pytz.UTC)

        current_day_start = datetime.combine(start_time.date(), workday_start)
        current_day_end = datetime.combine(start_time.date(), workday_end)

        # If operation starts before work hours, move to workday start
        if start_time < current_day_start:
            start_time = current_day_start

        end_time = start_time + duration

        # If operation ends after work hours, move to next workday
        if end_time > current_day_end:
            days_to_skip = 1 if datetime.now().weekday() != 4 else 3
            next_workday = current_day_start + timedelta(days=days_to_skip, minutes=10)
            start_time = next_workday
            end_time = start_time + duration

        return start_time, end_time

    @staticmethod
    def generate_optimized_plan() -> Response:
        pause = timedelta(minutes=5)

        operations: list[Operation] = OperationService._get_operations_to_distribute()
        for operation in operations:
            print(operation.exec_start)
        technicians: list[User] = UserService.get_technician_models()

        # Prepare data structures
        operations_by_product: dict[UUID, list[Operation]] = defaultdict(list)
        for op in operations:
            operations_by_product[op.product_id].append(op)

        # Initialize tech queues with their current assignments
        tech_queues: dict[str, list[tuple[datetime, UUID, User]]] = defaultdict(list)

        # First process all non-editable operations to set tech availability
        non_editable_ops = [op for op in operations if not op.is_exec_start_editable and op.exec_start and op.tech]
        for op in non_editable_ops:
            op_duration = timedelta(
                minutes=op.operation_type.exec_time.minute,
                hours=op.operation_type.exec_time.hour,
            )
            tech_end_time = op.exec_start + op_duration + pause
            heapq.heappush(tech_queues[op.tech.get_tech_group()], (tech_end_time, op.tech.id, op.tech))

        # Then add all remaining available techs
        for tech in technicians:
            # Only add if not already in queue (from non-editable ops)
            if not any(t.id == tech.id for queue in tech_queues.values() for (_, _, t) in queue):
                heapq.heappush(tech_queues[tech.get_tech_group()], (datetime.now(tz=pytz.UTC), tech.id, tech))

        ops_to_update: list[Operation] = []

        for product_id, product_ops in operations_by_product.items():
            for op in product_ops:
                # Skip operations that shouldn't be modified
                if not op.is_exec_start_editable:
                    continue

                if not tech_queues.get(op.operation_type.group):
                    raise ValueError(f"No available technician for operation type {op.operation_type.group}")

                available_time, tech_id, tech = heapq.heappop(tech_queues[op.operation_type.group])

                # Calculate start time
                start_time: datetime = available_time

                # Consider previous operations in product (both editable and non-editable)
                if op.ordinal_number > 1:
                    prev_ops = [o for o in operations_by_product[op.product_id]
                                if o.ordinal_number == op.ordinal_number - 1]
                    if prev_ops:
                        prev_op = prev_ops[0]
                        if prev_op.exec_start:
                            prev_duration = timedelta(
                                minutes=prev_op.operation_type.exec_time.minute,
                                hours=prev_op.operation_type.exec_time.hour,
                            )
                            prev_end = prev_op.exec_start + prev_duration + pause
                            start_time = max(start_time, prev_end)

                op_duration: timedelta = timedelta(
                    minutes=op.operation_type.exec_time.minute,
                    hours=op.operation_type.exec_time.hour,
                )

                start_time, end_time = OperationService._adjust_to_work_hours(start_time, op_duration)

                # Check deadline
                deadline: date = op.product.order.deadline
                deadline_as_datetime: datetime = datetime.combine(deadline, datetime.min.time(), tzinfo=pytz.UTC)
                if start_time + op_duration > deadline_as_datetime:
                    raise ValueError(f"Operation {op.id} would miss deadline")

                # Prepare for update
                op.exec_start = start_time
                op.tech = tech
                ops_to_update.append(op)

                # Update tech availability
                new_available_time = start_time + op_duration + pause
                heapq.heappush(tech_queues[tech.get_tech_group()], (new_available_time, tech.id, tech))

        preprocessed_operations = [
            OperationService._preprocess_operation_for_schedule(operation, with_tech=True) for operation in operations
        ]
        grouped_operations = OperationService._group_operations_by_product(preprocessed_operations)
        serializer = OperationForScheduleSerializer(grouped_operations, many=True)
        return Response(serializer.data)

    @staticmethod
    def apply_optimized_plan(request) -> Response:
        serializer = ApplyOperationsPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tech_email_tech = {}
        techs = User.objects.all()
        for tech in techs:
            tech_email_tech[tech.email] = tech

        operations_to_update = []
        for operation_schema in serializer.validated_data["operations"]:
            operation = Operation.objects.get(id=operation_schema["operation_id"])
            operation.tech_id = tech_email_tech[operation_schema["tech_email"]].id
            operation.exec_start = operation_schema["exec_start"]
            operations_to_update.append(operation)

        Operation.objects.bulk_update(
            operations_to_update,
            ['exec_start', 'tech_id'],
            batch_size=500,
        )

        return Response(status=status.HTTP_200_OK)
