from djmoney.contrib.django_rest_framework.fields import MoneyField
from rest_framework import serializers

from openinvoice.core.fields import CurrencyField
from openinvoice.core.validators import ExactlyOneValidator

from .choices import CouponStatus


class CouponSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField()
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    status = serializers.ChoiceField(choices=CouponStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    archived_at = serializers.DateTimeField(allow_null=True)


class CouponCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, required=False)

    class Meta:
        validators = [
            ExactlyOneValidator("amount", "percentage"),
        ]


class CouponUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
