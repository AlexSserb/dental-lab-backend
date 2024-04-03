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

from .serializers import *


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(request=UserSerializer, responses=CustomTokenObtainPairSerializer)
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


@extend_schema(responses=UserProfileSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfileData(request, email):
    user = get_object_or_404(get_user_model(), email=email)
    serializer = UserProfileSerializer(user)
    return Response({ **serializer.data, 'group': user.groups.values_list('name', flat=True).first() })
    

def edit_user_name(request, email, data, user_field):
    user = get_object_or_404(get_user_model(), email=email)
    
    if request.user.email != email:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if user_field == 'first_name':
        user.first_name = data
    elif user_field == 'last_name':
        user.last_name = data
    
    user.save()
    serializer = UserProfileSerializer(user)

    return Response({ **serializer.data, 'group': user.groups.values_list('name', flat=True).first() })


@extend_schema(responses=UserProfileSerializer)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editUserFirstName(request, email, name):
    return edit_user_name(request, email, name, 'first_name')


@extend_schema(responses=UserProfileSerializer)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editUserLastName(request, email, name):
    return edit_user_name(request, email, name, 'last_name')


@extend_schema(request=PasswordChangeSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def changePassword(request):
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user

        if user.check_password(serializer.validated_data['old_password']):
            user.set_password(request.data['new_password'])
            user.save()
            return Response(status=status.HTTP_200_OK)
        
        return Response({'old_password': ['Wrong password']}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
