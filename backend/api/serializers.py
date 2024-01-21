from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import *


User = get_user_model()


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ['id', 'name', 'exec_time']


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name']

class ProductStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatus
        fields = ['id', 'name']

class ToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = ['id', 'product', 'tooth_number']

class ProductSerializer(serializers.ModelSerializer):
    product_type = ProductTypeSerializer(read_only=True)
    product_status = ProductStatusSerializer(read_only=True)
    teeth = ToothSerializer(many=True)

    class Meta:
        model = Product
        fields = ['id', 'product_type', 'product_status', 'amount', 'teeth']


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'name']

class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'order_date']
