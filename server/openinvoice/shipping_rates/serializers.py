from djmoney.contrib.django_rest_framework.fields import MoneyField
from rest_framework import serializers

from openinvoice.core.fields import CurrencyField, MetadataField

from .choices import ShippingRateStatus


class ShippingRateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(allow_null=True, max_length=255)
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    status = serializers.ChoiceField(choices=ShippingRateStatus.choices)
    metadata = MetadataField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    archived_at = serializers.DateTimeField(allow_null=True)


class ShippingRateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=255, allow_null=True, required=False)
    currency = CurrencyField(required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    metadata = MetadataField(allow_null=True, required=False)


class ShippingRateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    code = serializers.CharField(max_length=255, allow_null=True, required=False)
    currency = CurrencyField(required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    metadata = MetadataField(required=False)
