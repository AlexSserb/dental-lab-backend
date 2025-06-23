from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
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
    MAX_ATTEMPTS = getattr(settings, "LOGIN_ATTEMPT_LIMIT", 5)
    LOCKOUT_TIME = getattr(settings, "LOGIN_LOCKOUT_SECONDS", 300)

    def _key(self, username: str) -> str:
        return f"failed_login::{username.casefold()}"

    def validate(self, attrs):
        username = attrs.get(self.username_field)

        # check if the user already locked
        attempts = cache.get(self._key(username), 0)
        if attempts >= self.MAX_ATTEMPTS:
            raise AuthenticationFailed(
                f"Слишком много попыток входа. "
                f"Попробуйте снова через {self.LOCKOUT_TIME // 60} минут."
            )

        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            attempts += 1
            cache.set(self._key(username), attempts, self.LOCKOUT_TIME)
            raise AuthenticationFailed(f"Неверный почтовый адрес или пароль")

        cache.delete(self._key(username))
        return data

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
    group_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "created_at", "customers", "group", "group_id"]

    def get_group(self, user):
        group = user.groups.values_list("name", flat=True).first()
        if not group:
            group = "Врач"
        return group

    def get_group_id(self, user) -> int:
        group_id = user.groups.values_list("id", flat=True).first()
        if not group_id:
            group_id = -1
        return group_id


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
