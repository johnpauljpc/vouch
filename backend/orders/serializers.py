from rest_framework import serializers
from django.db import transaction

from cart.models import Cart, CartItem
from products.models import Product
from .models import (
    Order,
    OrderItem,
    Address,
)

# Address
class AddrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'full_name', 'phone', 'address', 'city', 'state', 'country']


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
            "quantity": {"read_only": True},
            "sub_total": {"read_only": True},
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many = True, read_only =True)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            "total_amount",
            "status",
            "is_paid",
            "created_at",
            "updated_at",
            'items',
            "shipping_address"
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
        with price snapshots, validates stock, then clears the cart.
        """
        request = self.context["request"]
        user = request.user

        with transaction.atomic():
            cart = Cart.objects.filter(user=user).first()
            if not cart:
                raise serializers.ValidationError({"detail": "Cart is empty."})

            cart_items = list(
                CartItem.objects.filter(cart=cart)
                .select_for_update()
                .select_related("product")
            )
            if not cart_items:
                raise serializers.ValidationError({"detail": "Cart is empty."})

            # Lock product rows so concurrent checkouts can't oversell
            product_ids = [item.product_id for item in cart_items]
            locked_products = {
                p.id: p
                for p in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            address = Address.objects.get(id=validated_data["shipping_address_id"], user=user)

            order = Order.objects.create(
                user=user,
                shipping_address=address,
                status="pending",
                is_paid=False,
                total_amount=0,
            )

            total = 0
            order_items = []

            for item in cart_items:
                product = locked_products[item.product_id]
                qty = item.quantity

                if qty > product.stock:
                    raise serializers.ValidationError(
                        {"detail": f"Insufficient stock for {product.name}."}
                    )

                product.stock -= qty
                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        price=product.price,
                        quantity=qty,
                    )
                )
                total += product.price * qty

            Product.objects.bulk_update(locked_products.values(), ["stock"])
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
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ])

    def update(self, instance, validated_data):
        self.initial_status = instance.status
        instance.status = validated_data.get("status")
        instance.save(update_fields=['status'])
        return instance
    
    def to_representation(self, instance):
        
        return {
            'msg':'Order status successfully updated!',
            'previous_status':self.initial_status,
            'current_status': instance.status
        }


class OrderCancelSerializer(serializers.Serializer):


    def update(self, instance, validated_data):
        instance.status = 'cancelled'
        instance.save(update_fields=['status'])
        return instance
    

    
    def to_representation(self, instance):
        # return minimal response
        return {
            "id": instance.id,
            "status": instance.status,
            "is_paid": instance.is_paid,
            "total_amount": str(instance.total_amount),
        }
        