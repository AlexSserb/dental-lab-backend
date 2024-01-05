from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import *


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    class Meta:
        model = User
        fields = ['id', 'password', 'email']


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ['id', 'name', 'exec_time']
        