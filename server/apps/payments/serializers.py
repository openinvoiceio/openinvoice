from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceStatus
from apps.invoices.fields import InvoiceRelatedField
from common.fields import CurrencyField

from .choices import PaymentStatus


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    description = serializers.CharField(allow_null=True)
    transaction_id = serializers.CharField(allow_null=True)
    url = serializers.URLField(allow_null=True)
    message = serializers.CharField(allow_null=True)
    invoice_ids = serializers.SerializerMethodField()
    provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True)
    received_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()

    @extend_schema_field(serializers.ListField(child=serializers.UUIDField()))
    def get_invoice_ids(self, obj):
        return list(obj.invoices.values_list("id", flat=True))


class PaymentRecordSerializer(serializers.Serializer):
    invoice_id = InvoiceRelatedField(source="invoice")
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    description = serializers.CharField(allow_null=True, required=False)
    transaction_id = serializers.CharField(required=False)
    received_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_invoice_id(self, value):
        if value.status != InvoiceStatus.OPEN:
            raise serializers.ValidationError(f"Cannot record payment for invoice in status {value.status}")

        return value

    def validate(self, data):
        data["amount"] = Money(data["amount"], data["currency"])

        invoice = data["invoice"]
        amount = data["amount"]

        if amount > invoice.outstanding_amount:
            raise serializers.ValidationError({"amount": "Payment amount exceeds outstanding amount"})

        return data
