from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from products.models import TimeStampedModel, Product

# Create your models here.
User = get_user_model()


class Cart(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    @property 
    def total(self):
        # _total = [item.product.price * item.quantity for item in self.items]
        _total = sum(item.sub_total for item in self.items.all())
        return _total
    def __str__(self):
        return f"cart - {self.user} - {self.total}"
    
class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ['cart', 'product']
    @property
    def sub_total(self):
        total = self.product.price * self.quantity
        return total
    
    def __str__(self):
        return f"{self.product} x {self.quantity}"
    

