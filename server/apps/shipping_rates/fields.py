from rest_framework import serializers

from .models import ShippingRate


class ShippingRateRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return ShippingRate.objects.filter(account=account)
