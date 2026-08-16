from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from products.models import Product

from .models import Order


@receiver(pre_save, sender=Order)
def _capture_previous_status(sender, instance, **kwargs):
    if instance.pk is None:
        instance._previous_status = None
        return

    previous = (
        Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    )
    instance._previous_status = previous


@receiver(post_save, sender=Order)
def restore_stock_on_cancel(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_status", None)

    if instance.status != "cancelled":
        return
    if created or previous == "cancelled":
        return

    transaction.on_commit(lambda: _restore_stock(instance.pk))


def _restore_stock(order_id: int):
    order = Order.objects.get(pk=order_id)
    for item in order.items.iterator():
        Product.objects.filter(pk=item.product_id).update(
            stock=F("stock") + item.quantity
        )