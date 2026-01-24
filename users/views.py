from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import CustomUser
from .serializers import RegisterSerializer,  UserSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer



class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)