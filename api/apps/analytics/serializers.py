from rest_framework import serializers

from common.fields import CurrencyField


class GrossRevenueParamsSerializer(serializers.Serializer):
    date_after = serializers.DateField(required=False)
    date_before = serializers.DateField(required=False)
    currency = CurrencyField(required=False)
    customer_id = serializers.UUIDField(required=False)


class GrossRevenueSerializer(serializers.Serializer):
    date = serializers.DateField()
    currency = CurrencyField()
    total_amount = serializers.DecimalField(max_digits=19, decimal_places=2)
    invoice_count = serializers.IntegerField()


class OverdueBalanceParamsSerializer(serializers.Serializer):
    date_after = serializers.DateField(required=False)
    date_before = serializers.DateField(required=False)
    currency = CurrencyField(required=False)
    customer_id = serializers.UUIDField(required=False)


class OverdueBalanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    currency = CurrencyField()
    total_amount = serializers.DecimalField(max_digits=19, decimal_places=2)
    invoice_ids = serializers.ListField(child=serializers.UUIDField())
