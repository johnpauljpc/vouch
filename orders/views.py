from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Address, Order
from .serializers import AddrSerializer,CheckoutSerializer, OrderSerializer, OrderCancelSerializer, OrderStatusUpdateSerializer
from .permissions import Is_Admin


@extend_schema_view(
    get=extend_schema(
        description="Retrieve a list of addresses belonging to the authenticated user. "
                    "Results are ordered by newest first.",
        responses=AddrSerializer,
        tags=["Addresses"],
    ),
    post=extend_schema(
        description="Create a new address for the authenticated user. "
                    "Requires authentication and valid address data.",
        request=AddrSerializer,
        responses=AddrSerializer,
        tags=["Addresses"],
    ),
)
class AddressCreateListView(generics.ListCreateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = AddrSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-id')
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        description="Retrieve a single address belonging to the authenticated user by ID.",
        responses=AddrSerializer,
        tags=["Addresses"],
    ),
    put=extend_schema(
        description="Update an existing address belonging to the authenticated user. "
                    "Requires full object data in the request body.",
        request=AddrSerializer,
        responses=AddrSerializer,
        tags=["Addresses"],
    ),
    patch=extend_schema(
        description="Partially update an existing address belonging to the authenticated user. "
                    "Only include fields that need to be updated.",
        request=AddrSerializer,
        responses=AddrSerializer,
        tags=["Addresses"],
    ),
    delete=extend_schema(
        description="Delete an existing address belonging to the authenticated user by ID.",
        responses={204: None},
        tags=["Addresses"],
    ),
)
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a single user address.
    """
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

'''
GET /api/orders/

GET /api/orders/{id}/

POST /api/orders/{id}/cancel/
'''
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('shipping_address').prefetch_related('items').order_by('-id')

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
class CancelOrderView(generics.UpdateAPIView):
    serializer_class = OrderCancelSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, status = 'pending', is_paid= False)
    

class StatusUpdateView(generics.UpdateAPIView):
    '''
    Superusers can modify the order status
    '''
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, Is_Admin]
    serializer_class = OrderStatusUpdateSerializer
    http_method_names = ['patch']

    
