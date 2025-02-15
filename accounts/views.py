from django.core.handlers.wsgi import WSGIRequest
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.serializers import MessageSerializer
from .permissions import *
from .serializers import *
from .services.user_service import UserService


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


@extend_schema(
    operation_id="register",
    request=UserSerializer,
    responses=TokenPairSerializer,
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    return UserService.register(request)


@extend_schema(
    operation_id="send_email_verification",
    responses=MessageSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_email_verification(request: WSGIRequest):
    return UserService.send_email_verification(request, request.user)


@extend_schema(
    operation_id="verify_email",
    request=EmailVerificationSerializer,
)
@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request):
    return UserService.verify_email(request)


@extend_schema(
    operation_id="get_profile_data",
    responses=UserProfileSerializer,
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile_data(request, email: str):
    return UserService.get_profile_data(email)


@extend_schema(
    operation_id="edit_first_name",
    responses=UserProfileSerializer,
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="name",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_first_name(request, email: str, name: str):
    return UserService().edit_user_first_name(request, email, name)


@extend_schema(
    operation_id="edit_last_name",
    responses=UserProfileSerializer,
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="name",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_last_name(request, email: str, name: str):
    return UserService().edit_user_last_name(request, email, name)


@extend_schema(
    operation_id="change_password",
    request=PasswordChangeSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    return UserService.change_password(request)


@extend_schema(
    operation_id="get_technicians_by_group",
    responses=UserProfileSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="group_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_technicians_by_group(request, group_id: int):
    return UserService.get_technicians_by_group(group_id)


@extend_schema(
    operation_id="get_customers",
    responses=CustomerSerializer(many=True),
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_customers(request):
    customers = Customer.objects.filter(is_active=True)
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id="attach_customers_to_user",
    request=AttachCustomersToUserSerializer,
    responses=UserProfileSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attach_customers_to_user(request):
    return UserService.attach_customers(request)
