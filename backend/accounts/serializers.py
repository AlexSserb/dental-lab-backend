from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import *


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['group'] = user.groups.values_list('name', flat=True).first()
        return token


class UserSerializer(serializers.ModelSerializer):
    """
        Сериализатор для регистрации пользователя
    """
    id = serializers.UUIDField(required=False)
    class Meta:
        model = User
        fields = ['id', 'password', 'email', 'first_name', 'last_name']
        

class UserProfileSerializer(serializers.ModelSerializer):
    """
        Сериализатор для вывода данных в профиле пользователя
    """
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'created_at']
        