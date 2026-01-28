from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema

from .models import Address
from .serializers import AddrSerializer,CheckoutSerializer, OrderSerializers, OrderItemSerializer


class AddressCreateListView(generics.ListCreateAPIView):
    '''
    GET  /api/addresses/      -> list user's addresses
    POST /api/addresses/      -> create a new address for logged in user
    '''


    permission_classes = [IsAuthenticated]
    serializer_class = AddrSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-id')
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''
    GET    /api/addresses/{id}/   -> retrieve one of my addresses
    PATCH  /api/addresses/{id}/   -> update one of my addresses
    DELETE /api/addresses/{id}/   -> delete one of my addresses
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = AddrSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)




class CheckoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
