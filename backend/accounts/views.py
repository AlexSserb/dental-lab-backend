from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone
from django.http import Http404

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
    try:
        user =  User.objects.get(email=email)
        serializer = UserProfileSerializer(user)
        return Response({ **serializer.data, 'group': user.groups.values_list('name', flat=True).first() })
    except User.DoesNotExist:
        raise Http404
    