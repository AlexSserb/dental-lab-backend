from datetime import time

from rest_framework import serializers

from accounts.serializers import UserProfileSerializer
from operations.models import Operation
from works.models import WorkType, WorkStatus, Work


class WorkTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkType
        fields = ["id", "name", "cost"]


class WorkStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStatus
        fields = ["id", "name"]


class WorkSerializer(serializers.ModelSerializer):
    work_type = WorkTypeSerializer(read_only=True)
    work_status = WorkStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField("get_cost")
    discount = serializers.FloatField(required=True, min_value=0, max_value=100)
    amount = serializers.IntegerField(required=True, min_value=0)

    class Meta:
        model = Work
        fields = [
            "id",
            "work_type",
            "work_status",
            "discount",
            "amount",
            "cost",
            "teeth",
        ]

    def get_cost(self, obj: Work) -> float:
        return obj.get_cost()


from operations.serializers import OperationTypeSerializer, OperationStatusSerializer


class OperationForWorkSerializer(serializers.ModelSerializer):
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
            "exec_time",
        ]

    def get_exec_time(self, obj: Operation) -> time:
        return obj.get_exec_time()


class WorkAndOperationsSerializer(WorkSerializer):
    operations = OperationForWorkSerializer(many=True)

    class Meta:
        model = Work
        fields = [
            "id",
            "work_type",
            "work_status",
            "discount",
            "amount",
            "cost",
            "teeth",
            "operations",
        ]
