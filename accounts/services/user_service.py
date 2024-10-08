from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    AttachCustomersToUserSerializer,
)


class UserService:
    @staticmethod
    def register(request: WSGIRequest) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(email=request.data["email"])
            user.last_login = timezone.now()
            user.set_password(request.data["password"])
            user.save()

            refresh = CustomTokenObtainPairSerializer.get_token(user)

            return Response({"refresh": str(refresh), "access": str(refresh.access_token)})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_profile_data(email: str) -> Response:
        user = get_object_or_404(get_user_model(), email=email)
        serializer = UserProfileSerializer(user)

        group = user.groups.values_list("name", flat=True).first()
        if not group:
            group = "Врач"

        return Response({**serializer.data, "group": group})

    @staticmethod
    def _edit_user_name(request: WSGIRequest, email: str, data: str, user_field: str) -> Response:
        user = get_object_or_404(get_user_model(), email=email)

        if request.user.email != email:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if user_field == "first_name":
            user.first_name = data
        elif user_field == "last_name":
            user.last_name = data

        user.save()
        serializer = UserProfileSerializer(user)

        return Response({**serializer.data, "group": user.groups.values_list("name", flat=True).first()})

    def edit_user_first_name(self, request: WSGIRequest, email: str, name: str) -> Response:
        return self._edit_user_name(request, email, name, "first_name")

    def edit_user_last_name(self, request: WSGIRequest, email: str, name: str) -> Response:
        return self._edit_user_name(request, email, name, "last_name")

    @staticmethod
    def change_password(request: WSGIRequest) -> Response:
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            if user.check_password(serializer.validated_data["old_password"]):
                user.set_password(request.data["new_password"])
                user.save()
                return Response(status=status.HTTP_200_OK)

            return Response({"old_password": ["Wrong password"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_technicians_by_group(group_id: int) -> Response:
        technicians = User.objects.filter(groups__id__in=[group_id, 3])
        serializer = UserProfileSerializer(technicians, many=True)
        return Response(serializer.data)

    @staticmethod
    def attach_customers(request: WSGIRequest) -> Response:
        serializer = AttachCustomersToUserSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            customers = serializer.validated_data["customers"]
            user.customers.clear()
            user.customers.add(*customers)

            serializer = UserProfileSerializer(user)

            return Response(
                {
                    **serializer.data,
                    "group": user.groups.values_list("name", flat=True).first(),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
