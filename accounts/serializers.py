from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import Token, RefreshToken

from .models import *


def get_tokens_with_payload(token: Token, user: User) -> Token:
    token["email"] = user.email
    token["isActive"] = user.is_active
    token["isVerified"] = user.is_verified

    group = user.groups.first()
    if group:
        token["group"], token["groupId"] = group.name, group.id
    else:
        token["group"], token["groupId"] = "Врач", 0

    return token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User) -> Token:
        token = super().get_token(user)

        return get_tokens_with_payload(token, user)


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = attrs['refresh']

        old_token = RefreshToken(refresh)
        user = User.objects.get(email=old_token["email"])
        token = get_tokens_with_payload(old_token, user)

        return {
            'access': str(token.access_token),
            'refresh': str(token),
        }


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
            "is_verified",
            "is_active",
            "customers",
        ]


class EmailVerificationSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=510, read_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода данных в профиле пользователя
    """

    customers = CustomerSerializer(many=True)
    group = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "created_at", "customers", "group"]

    def get_group(self, user):
        group = user.groups.values_list("name", flat=True).first()
        if not group:
            group = "Врач"
        return group


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
