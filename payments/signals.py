from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Payment
from orders.models import Order  # change to your real import
from .utils.receipt_service import generate_upload_and_email_receipt_sync


@receiver(post_save, sender=Payment)
def on_payment_success_generate_receipt(sender, instance: Payment, **kwargs):
    # Only when payment is successful
    if instance.status != "success":
        return

    order_id = instance.order_id

    def _run():
        order = Order.objects.get(id=order_id)

        # extra idempotency guard
        if hasattr(order, "receipt") and order.receipt.cloudinary_url and order.receipt.emailed_at:
            return

        generate_upload_and_email_receipt_sync(order)

    # Run only after the save is fully committed
    transaction.on_commit(_run)
