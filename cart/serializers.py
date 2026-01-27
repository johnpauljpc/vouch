from rest_framework import serializers
from .models import Cart, CartItem


class AddCartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField(source="product.price")
    sub_total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "price", "quantity", "sub_total"]


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField(source="product.price")
    sub_total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "product_name", "price", "quantity", "sub_total"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Cart
        fields = ["id", "items", "user", "total"]


