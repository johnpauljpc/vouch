
# payments/signals.py
import logging
from threading import Thread

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def on_payment_success_generate_receipt(sender, instance: Payment, **kwargs):
    # Only when payment is successful
    if instance.status != "success":
        return

    order_id = instance.order_id

    def _background_job(order_id: int):
        """
        Runs outside the request thread.
        Fetches fresh DB objects inside this thread.
        """
        from orders.models import Order
        from .utils.receipt_service import generate_upload_and_email_receipt_sync

        try:
            order = Order.objects.select_related("user").get(id=order_id)

            # idempotency guard
            receipt = getattr(order, "receipt", None)
            if receipt and receipt.cloudinary_url and receipt.emailed_at:
                return

            generate_upload_and_email_receipt_sync(order)

        except Exception:
            logger.exception("Receipt generation failed for order_id=%s", order_id)

    def _on_commit():
        Thread(target=_background_job, args=(order_id,), daemon=True).start()

    transaction.on_commit(_on_commit)
