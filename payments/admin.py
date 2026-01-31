from django.contrib import admin

from .models import Payment

# Register your models here.
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = ['order', 'reference', 'amount', 'status']


