from datetime import time

from rest_framework import serializers

from accounts.serializers import UserProfileSerializer
from core.serializers import PaginationSerializer
from operations.models import OperationType, OperationStatus, Operation, OperationEvent
from orders.models import Order
from orders.serializers import OrderFileSerializer


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ["id", "name", "exec_time_per_item", "fixed_exec_time", "group"]


class OperationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationStatus
        fields = ["id", "name", "number"]


class OperationEventSerializer(serializers.ModelSerializer):
    operation_status = OperationStatusSerializer(read_only=True)

    class Meta:
        model = OperationEvent
        fields = ["operation_status", "pgh_created_at"]


class FullOperationSerializer(serializers.ModelSerializer):
    history = OperationEventSerializer(many=True)
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    tech = UserProfileSerializer()
    exec_time = serializers.SerializerMethodField("get_exec_time")

    class Meta:
        model = Operation
        fields = [
            "id",
            "operation_type",
            "operation_status",
            "tech",
            "exec_start",
            "ordinal_number",
            "history",
            "is_exec_start_editable",
            "exec_time",
        ]

    def get_exec_time(self, obj: Operation) -> time:
        return obj.get_exec_time()


from works.serializers import WorkSerializer


class OperationSerializer(serializers.ModelSerializer):
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    work = WorkSerializer()
    exec_time = serializers.SerializerMethodField("get_exec_time")
    files = serializers.SerializerMethodField("get_files")
    color = serializers.SerializerMethodField("get_color")

    class Meta:
        model = Operation
        fields = [
            "id",
            "operation_type",
            "operation_status",
            "work",
            "exec_start",
            "ordinal_number",
            "is_exec_start_editable",
            "exec_time",
            "files",
            "color",
        ]

    def get_exec_time(self, obj: Operation) -> time:
        return obj.get_exec_time()

    def get_files(self, obj: Operation) -> OrderFileSerializer(many=True):
        order = obj.work.order
        order_files = order.files.all()
        return OrderFileSerializer(order_files, many=True).data

    def get_color(self, obj: Operation) -> str:
        return obj.work.order.tooth_color


class OperationsPaginatedListSerializer(PaginationSerializer):
    results = OperationSerializer(many=True)


class OperationForTechScheduleSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    work = WorkSerializer(required=True)
    editable = serializers.BooleanField(required=True)
    exec_time = serializers.TimeField(required=True)


class OperationForScheduleSerializer(OperationForTechScheduleSerializer):
    resource_id = serializers.UUIDField()
    error = serializers.BooleanField()
    error_description = serializers.CharField()


class SetOperationDataSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    tech_email = serializers.CharField(required=False)
    exec_start = serializers.DateTimeField(required=False)
    editable = serializers.BooleanField(required=False)


class AssignOperationSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    exec_start = serializers.CharField(required=True)
    tech_email = serializers.CharField(required=True)


class UpdateOperationStatusSerializer(serializers.Serializer):
    status = serializers.PrimaryKeyRelatedField(
        queryset=OperationStatus.objects.all(),
        pk_field=serializers.UUIDField(),
    )


class ApplyOperationsSerializer(serializers.Serializer):
    operation_id = serializers.CharField(required=True)
    tech_email = serializers.CharField(required=True)
    exec_start = serializers.DateTimeField(required=True)


class ApplyOperationsPlanSerializer(serializers.Serializer):
    operations = ApplyOperationsSerializer(many=True)


class AssignOrderOperations(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        pk_field=serializers.UUIDField(),
    )
