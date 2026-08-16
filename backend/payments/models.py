from django.db import models
from django.utils import timezone

from orders.models import Order
from products.models import TimeStampedModel

# Create your models here.
class Payment(models.Model):
    PAYMENT_STATUS = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    reference = models.CharField(max_length=200, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.reference} - {self.status}"




class Receipt(TimeStampedModel):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=50, unique=True)

    cloudinary_url = models.URLField(blank=True, default="")
    cloudinary_public_id = models.CharField(max_length=200, blank=True, default="")

    emailed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    def mark_emailed(self):
        self.emailed_at = timezone.now()
        self.save(update_fields=["emailed_at"])