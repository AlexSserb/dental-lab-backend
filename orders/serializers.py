from rest_framework import serializers

from accounts.models import Customer
from accounts.serializers import UserProfileSerializer, CustomerSerializer
from core.serializers import PaginationSerializer
from .models import *

User = get_user_model()


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer()
    cost = serializers.SerializerMethodField("get_cost")
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = ["id", "status", "order_date", "discount", "cost", "comment", "customer", "deadline",
                  "comment_after_accept"]

    def get_cost(self, obj: Order) -> float:
        return obj.get_cost()


class OrdersPaginatedListSerializer(PaginationSerializer):
    results = OrderSerializer(many=True)


class OrderWithPhysicianSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField("get_cost")
    user = UserProfileSerializer()
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = ["id", "status", "order_date", "discount", "cost", "user", "comment", "customer", "deadline",
                  "comment_after_accept"]

    def get_cost(self, obj: Order) -> float:
        return obj.get_cost()


class ProductFromUserSerializer(serializers.Serializer):
    product_type_id = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True, min_value=1)
    teeth = serializers.ListField(child=serializers.IntegerField(min_value=11, max_value=48), required=True)


class DataForOrderCreationSerializer(serializers.Serializer):
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), pk_field=serializers.UUIDField())
    product_types = ProductFromUserSerializer(many=True)
    comment = serializers.CharField(default="", max_length=512, allow_blank=True)


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.PrimaryKeyRelatedField(queryset=OrderStatus.objects.all(), pk_field=serializers.UUIDField())


class DiscountSetterSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    discount = serializers.IntegerField(required=True, min_value=0, max_value=100)


class OrderDiscountSetterSerializer(serializers.Serializer):
    order_discount_data = DiscountSetterSerializer()
    products_discounts_data = DiscountSetterSerializer(many=True)


class ReportDefectSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), pk_field=serializers.UUIDField())
    comment_after_accept = serializers.CharField(max_length=500, allow_blank=True, default="")
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), pk_field=serializers.UUIDField(),
                                                  many=True)


class CancelOrderSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), pk_field=serializers.UUIDField())
