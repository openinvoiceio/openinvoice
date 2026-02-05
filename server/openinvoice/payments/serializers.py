from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from openinvoice.core.fields import CurrencyField
from openinvoice.integrations.choices import PaymentProvider
from openinvoice.invoices.choices import InvoiceStatus
from openinvoice.invoices.fields import InvoiceRelatedField

from .choices import PaymentStatus
from .models import Payment


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    description = serializers.CharField(allow_null=True)
    transaction_id = serializers.CharField(allow_null=True)
    url = serializers.URLField(allow_null=True)
    message = serializers.CharField(allow_null=True)
    invoices = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True)
    received_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()

    class Meta:
        model = Payment


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
