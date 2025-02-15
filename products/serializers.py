from rest_framework import serializers

from accounts.serializers import UserProfileSerializer
from operations.models import Operation
from products.models import ProductType, ProductStatus, Product


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
    discount = serializers.FloatField(required=True, min_value=0, max_value=100)
    amount = serializers.IntegerField(required=True, min_value=0)

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

    def get_cost(self, obj: Product) -> float:
        return obj.get_cost()


from operations.serializers import OperationTypeSerializer, OperationStatusSerializer


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
