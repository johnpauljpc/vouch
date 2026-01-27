from rest_framework import serializers
from django.db import transaction

from .models import (
    Cart,
    Order,
    OrderItem,
    Address,
)


# ORDERS
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "product_name",
            "product",
            "price",
            "quantity",
            "sub_total",
        ]
        extra_kwargs = {
            "price": {"read_only": True},
            "quantity": {"reaad_only": True},
            "sub_total": {"reaad_only": True},
        }


class OrderSerializers(serializers.ModelSerializer):
    items = OrderItemSerializer(many = True, read_only =True)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "user",
            "shipping_address",
            "total_amount",
            "status",
            "is_paid",
            "created_at",
            "updated_at",
            'items'
        ]

    def get_shipping_address(self, obj):
        addr = getattr(obj, 'shipping_address', None)

        if not addr:
            return None
        
        return {
        "id": addr.id,
        "full_name": addr.full_name,
        "phone": addr.phone,
        "address": addr.address,
        "city": addr.city,
        "state": addr.state,
        "country": addr.country,
        }




class CheckoutSerializer(serializers.Serializer):
    shipping_address_id = serializers.IntegerField()

    def validate_shipping_address_id(self, value):
        request = self.context["request"]
        if not Address.objects.filter(id=value, user=request.user).exists():
            raise serializers.ValidationError("Invalid address for this user.")
        return value

    def create(self, validated_data):
        """
        Converts the authenticated user's cart into an Order + OrderItems
        with price snapshots, then clears the cart.
        """
        request = self.context["request"]
        user = request.user

        cart = Cart.objects.filter(user=user).prefetch_related("items__product").first()
        if not cart or cart.items.count() == 0:
            raise serializers.ValidationError({"detail": "Cart is empty."})

        address = Address.objects.get(id=validated_data["shipping_address_id"], user=user)

        with transaction.atomic():
            # Create order first
            order = Order.objects.create(
                user=user,
                shipping_address=address,   
                status="pending",
                is_paid=False,
                total_amount=0,
            )

            total = 0
            order_items = []

            for item in cart.items.all():
                product = item.product
                price_snapshot = product.price
                qty = item.quantity

                order_item = OrderItem(
                    order=order,
                    product=product,
                    price=price_snapshot,
                    quantity=qty,
                )
                order_items.append(order_item)
                total += price_snapshot * qty

            OrderItem.objects.bulk_create(order_items)

            order.total_amount = total
            order.save(update_fields=["total_amount"])

            # Clear cart after order is created
            cart.items.all().delete()

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ])