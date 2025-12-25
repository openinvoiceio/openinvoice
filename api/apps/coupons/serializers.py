from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers

from common.fields import CurrencyField


class CouponSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField()
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class CouponCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, required=False)

    def validate(self, data):
        amount = data.get("amount")
        percentage = data.get("percentage")

        if amount is None and percentage is None:
            raise serializers.ValidationError("Either amount or percentage must be provided.")

        if amount is not None and percentage is not None:
            raise serializers.ValidationError("Amount and percentage are mutually exclusive.")

        return data


class CouponUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
