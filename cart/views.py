from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


from .models import Cart, CartItem
from products.models import  Product
from .serializers import CartSerializer, CartItemSerializer, AddCartItemSerializer
# Create your views here.

class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AddCartItemSerializer)
    def post(self, request):
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
 

        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
           defaults={'quantity':quantity}
        )

        if not created:
            item.quantity += quantity
            item.save()

        serializer = AddCartItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, cart__user = request.user)
        serializer = CartItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # TO update
    @extend_schema(request=CartItemSerializer)
    def put(self, request, item_id):
        item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
        )

        quantity = request.data.get("quantity")

        if not quantity or int(quantity) < 1:
            return Response(
                {"detail": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = int(quantity)
        item.save()

        serializer = CartItemSerializer(item)
        return Response(serializer.data)

    # TO delete
    def delete(self, request, item_id):
        item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
        )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response(
            {"detail": "Cart cleared"},
            status=status.HTTP_204_NO_CONTENT,
        )

