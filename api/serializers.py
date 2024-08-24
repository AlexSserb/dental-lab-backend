from rest_framework import serializers

from accounts.models import Customer
from accounts.serializers import UserProfileSerializer, CustomerSerializer
from .models import *

User = get_user_model()


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = "__all__"


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ["id", "name", "exec_time", "group"]


class OperationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationStatus
        fields = ["id", "name", "number"]


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ["id", "name", "cost"]


class ProductStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatus
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    product_type = ProductTypeSerializer(read_only=True)
    product_status = ProductStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField("get_cost")

    class Meta:
        model = Product
        fields = [
            "id",
            "product_type",
            "product_status",
            "discount",
            "amount",
            "cost",
            "teeth",
        ]

    def get_cost(self, obj):
        return obj.get_cost()


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ["id", "name", "number"]


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer()
    cost = serializers.SerializerMethodField("get_cost")
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = ["id", "status", "order_date", "discount", "cost", "customer"]

    def get_cost(self, obj):
        return obj.get_cost()


class OrderWithPhysicianSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField("get_cost")
    user = UserProfileSerializer()
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = ["id", "status", "order_date", "discount", "cost", "user", "customer"]

    def get_cost(self, obj):
        return obj.get_cost()


class ProductFromUserSerializer(serializers.Serializer):
    product_type_id = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True, min_value=1)
    teeth = serializers.ListField(child=serializers.IntegerField(min_value=11, max_value=48), required=True)


class DataForOrderCreationSerializer(serializers.Serializer):
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), pk_field=serializers.UUIDField())
    product_types = ProductFromUserSerializer(many=True)


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
        ]


class OperationForScheduleSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    product = ProductSerializer(required=True)


class OperationEventSerializer(serializers.ModelSerializer):
    operation_status = OperationStatusSerializer(read_only=True)

    class Meta:
        model = OperationEvent
        fields = ["operation_status", "pgh_created_at"]


class OperationForProductSerializer(serializers.ModelSerializer):
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
        ]


class AssignOperationSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    exec_start = serializers.CharField(required=True)
    tech_email = serializers.CharField(required=True)


class UpdateOperationStatusSerializer(serializers.Serializer):
    status_id = serializers.UUIDField(required=True)


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.PrimaryKeyRelatedField(queryset=OrderStatus.objects.all(), pk_field=serializers.UUIDField())


class ProductAndOperationsSerializer(ProductSerializer):
    operations = OperationForProductSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_type",
            "product_status",
            "discount",
            "amount",
            "cost",
            "teeth",
            "operations",
        ]


class DiscountSetterSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    discount = serializers.IntegerField(required=True, min_value=0, max_value=100)


class OrderDiscountSetterSerializer(serializers.Serializer):
    order = DiscountSetterSerializer()
    products = DiscountSetterSerializer(many=True)
