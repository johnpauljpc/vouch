from rest_framework import serializers
from .models import Cart, CartItem


class AddCartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField(source="product.price")
  

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "price", "quantity", "sub_total"]

        extra_kwargs = {
            "sub_total":{'read_only':True}
        }

    def validate(self, attrs):
        product = attrs.get("product")
        quantity = attrs.get("quantity")
        if product is not None and quantity is not None and quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} in stock."}
            )
        return attrs


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField(source="product.price")
    sub_total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "product_name", "price", "quantity", "sub_total"]

    def validate(self, attrs):
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        product = getattr(self.instance, "product", None)
        if product is not None and quantity is not None and quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} in stock."}
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Cart
        fields = ["id", "items", "user", "total"]


