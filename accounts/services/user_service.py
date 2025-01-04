import jwt
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import Token, AccessToken

from accounts import models
from accounts.models import User
from accounts.serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    AttachCustomersToUserSerializer,
)
from accounts.utils import Util
from app.settings import CLIENT_URL


class UserService:
    @staticmethod
    def send_email_verification(request: WSGIRequest, user: User):
        tokens = CustomTokenObtainPairSerializer.get_token(user)

        current_site = get_current_site(request).domain
        relative_link = reverse('verify-email')
        absurl = 'http://'+current_site+relative_link+"?token="+str(tokens.access_token)
        email_body = (
            f"Здравствуйте, {user.first_name} {user.last_name}!\n"
            f"Перейдите по этой ссылке для подтверждения почты:\n{absurl}"
        )
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'InColor - Подтверждение почты'
        }

        Util.send_email(data=data)

        return Response({"message": "Сообщение для подтверждения почты отправлено"})

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
            UserService.send_email_verification(request, user)

            return Response({"refresh": str(refresh), "access": str(refresh.access_token)})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def verify_email(request: WSGIRequest) -> Response:
        token = request.GET.get('token')
        context = {
            "path_to_app": CLIENT_URL + "registration"
        }
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user = models.User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return render(request, 'email_verification/success.html', context)
        except jwt.ExpiredSignatureError:
            context["error_details"] = "Время действия ссылки истекло."
            return render(request, 'email_verification/error.html', context)
        except jwt.exceptions.DecodeError:
            context["error_details"] = "Ссылка не корректна."
            return render(request, 'email_verification/error.html', context)

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
        technicians = User.objects.filter(groups__id=group_id)
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
