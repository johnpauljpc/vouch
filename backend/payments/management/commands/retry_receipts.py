from django.core.management.base import BaseCommand

from payments.models import Receipt
from payments.utils.receipt_service import generate_upload_and_email_receipt_sync


class Command(BaseCommand):
    help = "Retry generating/uploading/emailing receipts that previously failed."

    def handle(self, *args, **options):
        failed = list(
            Receipt.objects.filter(
                last_error__gt="", emailed_at__isnull=True
            ).select_related("order", "order__user")
        )

        if not failed:
            self.stdout.write("No failed receipts to retry.")
            return

        succeeded = 0
        for receipt in failed:
            try:
                generate_upload_and_email_receipt_sync(receipt.order)
                succeeded += 1
                self.stdout.write(self.style.SUCCESS(f"Order {receipt.order_id}: OK"))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Order {receipt.order_id}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Retried {len(failed)} receipts, {succeeded} succeeded.")
        )