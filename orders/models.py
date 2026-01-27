from django.db import models
from django.contrib.auth import get_user_model

from products.models import TimeStampedModel, Product

# Create your models here.
User = get_user_model()
    

class Order(TimeStampedModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    shipping_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True,blank=True )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default = 0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.user} - {self.status}"
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def sub_total(self):
        return self.price * self.quantity
    



class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Nigeria")

    def __str__(self):
        return f"{self.full_name} - {self.city}"


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
