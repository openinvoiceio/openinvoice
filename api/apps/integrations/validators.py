from rest_framework import serializers
from rest_framework.fields import Field

from .enums import PaymentProvider
from .models import StripeConnection


class PaymentProviderConnected:
    requires_context = True

    def __call__(self, value: PaymentProvider | None, serializer_field: Field):
        if value is None:
            return

        account = serializer_field.context["request"].account
        error = serializers.ValidationError("Payment provider connection not found")

        match value:
            case PaymentProvider.STRIPE:
                try:
                    StripeConnection.objects.get(account=account)
                except StripeConnection.DoesNotExist as e:
                    raise error from e
