from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, AddCartItemSerializer


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
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity},
        )

        if not created:
            item.quantity = min(product.stock, item.quantity + quantity)
            item.save()

        return Response(AddCartItemSerializer(item).data, status=status.HTTP_201_CREATED)


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

        serializer = CartItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

