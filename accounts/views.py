from typing import Type

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.reports.order_report import OrderReport
from orders.models import Order
from .permissions import *
from .reports.acceptance_report import AcceptanceReport
from .reports.invoice_for_payment import InvoiceForPayment
from .reports.report import Report
from .serializers import *
from .services.user_service import UserService


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


@extend_schema(request=UserSerializer, responses=CustomTokenObtainPairSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    return UserService.register(request)


@extend_schema(request=UserSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_email_verification(request):
    return UserService.send_email_verification(request, request.user)


@extend_schema(request=EmailVerificationSerializer)
@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request):
    return UserService.verify_email(request)


@extend_schema(responses=UserProfileSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile_data(request, email: str):
    return UserService.get_profile_data(email)


@extend_schema(responses=UserProfileSerializer)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_first_name(request, email: str, name: str):
    return UserService().edit_user_first_name(request, email, name)


@extend_schema(responses=UserProfileSerializer)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_user_last_name(request, email: str, name: str):
    return UserService().edit_user_last_name(request, email, name)


@extend_schema(request=PasswordChangeSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    return UserService.change_password(request)


@extend_schema(responses=UserProfileSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_technicians_by_group(request, group_id: int):
    return UserService.get_technicians_by_group(group_id)


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
    return UserService.attach_customers(request)


def get_order(order_id: str, report_class: Type[Report]):
    order = Order.objects.get(id=order_id)
    dental_lab_data = DentalLabData.objects.get()
    report = report_class(order, dental_lab_data)
    response = HttpResponse(bytes(report.output()), content_type="application/pdf")
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order_report(request, order_id: str):
    return get_order(order_id, OrderReport)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_acceptance_report(request, order_id: str):
    return get_order(order_id, AcceptanceReport)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoice_for_payment(request, order_id: str):
    return get_order(order_id, InvoiceForPayment)
