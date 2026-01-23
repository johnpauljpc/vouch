from rest_framework import serializers
from .models import (Cart, CartItem, Order,
                     OrderItem, Address, )

class CartSerializer(serializers.ModelSerializer):
    model = Cart
    fields = "__all__"

class CartItemSerializer(serializers.ModelSerializer):
    model = CartItem
    fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    model = Order
    fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    model = OrderItem
    fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    model = Address
    fields = "__all__"