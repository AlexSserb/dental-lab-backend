from .serializers import *
from .permissions import *

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.views.generic.list import ListView
from django.utils import timezone

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(email=request.data['email'])
        user.last_login = timezone.now()
        user.set_password(request.data['password'])
        user.save()
        
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        return Response({ 'refresh': str(refresh), 'access': str(refresh.access_token) })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperationTypeList(APIView):
    serializer_class = OperationTypeSerializer
    permission_classes = [IsDirector | IsLabAdmin | IsChiefTech | IsTech]

    def get(self, request, *args, **kwargs):
        operation_types = OperationType.objects.all()
        serializer = self.serializer_class(operation_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OperationTypeDetail(APIView):
    """
    Retrieve, update or delete an operation type instance.
    """
    permission_classes = [IsDirector | IsLabAdmin | IsChiefTech]
    serializer_class = OperationTypeSerializer

    def get_object(self, pk):
        try:
            return OperationType.objects.get(pk=pk)
        except OperationType.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        oper_type = self.get_object(pk)
        oper_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfileData(request):
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response({ **serializer.data, 'group': user.groups.values_list('name', flat=True).first() })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrdersForUser(request):
    user = request.user
    orders = Order.objects.filter(user=user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def getProductsForOrder(request, pk):
    products = Product.objects.filter(order=pk)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)