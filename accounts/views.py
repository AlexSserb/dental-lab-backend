from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django.utils import timezone

from .permissions import *
from .serializers import *


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(request=UserSerializer, responses=CustomTokenObtainPairSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
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


@extend_schema(responses=UserProfileSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile_data(request, email):
    user = get_object_or_404(get_user_model(), email=email)
    serializer = UserProfileSerializer(user)

    group = user.groups.values_list("name", flat=True).first()
    if not group:
        group = "Врач"

    return Response({**serializer.data, "group": group})


def edit_user_name(request, email, data, user_field):
    user = get_object_or_404(get_user_model(), email=email)

    if request.user.email != email:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if user_field == "first_name":
        user.first_name = data
    elif user_field == "last_name":
        user.last_name = data

    user.save()
    serializer = UserProfileSerializer(user)

    return Response(
        {**serializer.data, "group": user.groups.values_list("name", flat=True).first()}
    )


@extend_schema(responses=UserProfileSerializer)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_first_name(request, email, name):
    return edit_user_name(request, email, name, "first_name")


@extend_schema(responses=UserProfileSerializer)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_last_name(request, email, name):
    return edit_user_name(request, email, name, "last_name")


@extend_schema(request=PasswordChangeSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user

        if user.check_password(serializer.validated_data["old_password"]):
            user.set_password(request.data["new_password"])
            user.save()
            return Response(status=status.HTTP_200_OK)

        return Response(
            {"old_password": ["Wrong password"]}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=UserProfileSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsChiefTech | IsLabAdmin | IsDirector])
def get_technicians_by_group(request, group_id):
    technicians = User.objects.filter(groups__id__in=[group_id, 3])
    serializer = UserProfileSerializer(technicians, many=True)
    return Response(serializer.data)


@extend_schema(responses=CustomerSerializer(many=True))
@api_view(["GET"])
@permission_classes([AllowAny])
def get_customers(request):
    customers = Customer.objects.filter(is_active=True)
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)


@extend_schema(request=AttachCustomersToUserSerializer, responses=UserProfileSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attach_customers_to_user(request):
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
