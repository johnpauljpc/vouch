from rest_framework import serializers

from .models import Payment

class InitiateSquadPaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()