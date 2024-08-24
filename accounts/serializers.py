from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import *


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email

        group = user.groups.first()
        if group:
            token["group"], token["groupId"] = group.name, group.id
        else:
            token["group"], token["groupId"] = "Врач", 0

        return token


class CustomerSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заказчика (клиники, больницы)
    """

    class Meta:
        model = Customer
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя
    """

    id = serializers.UUIDField(required=False)
    customers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Customer.objects.all(), pk_field=serializers.UUIDField()
    )

    class Meta:
        model = User
        fields = [
            "id",
            "password",
            "email",
            "first_name",
            "last_name",
            "customers",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода данных в профиле пользователя
    """

    customers = CustomerSerializer(many=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "created_at", "customers"]


class UserEditProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для редактирования данных в профиле пользователя
    """

    group_id = serializers.IntegerField(min_value=1, max_value=7)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "group_id"]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля пользователя
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


class AttachCustomersToUserSerializer(serializers.Serializer):
    """
    Сериализатор для прикрепления организаций к пользователю
    """

    customers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Customer.objects.all(), pk_field=serializers.UUIDField()
    )

class ReportSerializer(serializers.ModelSerializer):
    report = serializers.FileField(required=True)
