from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema

from .serializers import CheckoutSerializer, OrderSerializers, OrderItemSerializer


class CheckoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
