from rest_framework import serializers

from accounts.serializers import UserProfileSerializer
from core.serializers import PaginationSerializer
from operations.models import OperationType, OperationStatus, Operation, OperationEvent


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ["id", "name", "exec_time", "group"]


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
        ]


from products.serializers import ProductSerializer


class OperationSerializer(serializers.ModelSerializer):
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    product = ProductSerializer()

    class Meta:
        model = Operation
        fields = [
            "id",
            "operation_type",
            "operation_status",
            "product",
            "exec_start",
            "ordinal_number",
            "is_exec_start_editable",
        ]


class OperationsPaginatedListSerializer(PaginationSerializer):
    results = OperationSerializer(many=True)


class OperationForTechScheduleSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    product = ProductSerializer(required=True)
    editable = serializers.BooleanField(required=True)


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
