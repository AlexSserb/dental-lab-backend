from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import *


User = get_user_model()


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ['id', 'name', 'exec_time']

class OperationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationStatus
        fields = ['id', 'name']


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name', 'cost']

class ProductStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatus
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    product_type = ProductTypeSerializer(read_only=True)
    product_status = ProductStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField('get_cost')

    class Meta:
        model = Product
        fields = ['id', 'product_type', 'product_status', 'discount', 'amount', 'cost', 'teeth']

    def get_cost(self, obj):
        return obj.get_cost()


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'name']

class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    cost = serializers.SerializerMethodField('get_cost')

    class Meta:
        model = Order
        fields = ['id', 'status', 'order_date', 'discount', 'cost']

    def get_cost(self, obj):
        return obj.get_cost()


class ProductFromUserSerializer(serializers.Serializer):
    product_type_id = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True, min_value=1)
    teeth = serializers.ListField(child=serializers.IntegerField(min_value=11, max_value=48), required=True)
    
class ManyProductsFromUserSerializer(serializers.Serializer):
    product_types = ProductFromUserSerializer(many=True)


class OperationSerializer(serializers.ModelSerializer):
    operation_type = OperationTypeSerializer(required=True)
    operation_status = OperationStatusSerializer(required=True)
    product = ProductSerializer()

    class Meta:
        model = Operation
        fields = ['id', 'operation_type', 'operation_status', 'product']

class UpdateOperationStatusSerializer(serializers.Serializer):
    status_id = serializers.UUIDField(required=True)
