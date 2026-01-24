from decimal import Decimal

from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from apps.addresses.serializers import AddressSerializer
from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceStatus
from apps.invoices.fields import InvoiceLineRelatedField, InvoiceRelatedField
from apps.numbering_systems.choices import NumberingSystemAppliesTo
from apps.numbering_systems.fields import NumberingSystemRelatedField
from apps.tax_ids.serializers import TaxIdSerializer
from apps.tax_rates.fields import TaxRateRelatedField
from common.access import has_feature
from common.calculations import clamp_money
from common.choices import FeatureCode
from common.fields import CurrencyField, MetadataField

from .calculations import calculate_credit_note_line_amounts
from .choices import CreditNoteDeliveryMethod, CreditNoteReason, CreditNoteStatus
from .fields import CreditNoteRelatedField


class CreditNoteCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    logo_id = serializers.UUIDField(allow_null=True)
    tax_ids = TaxIdSerializer(many=True, read_only=True)


class CreditNoteAccountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    logo_id = serializers.UUIDField(allow_null=True)
    tax_ids = TaxIdSerializer(many=True, read_only=True)


class CreditNoteLineTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class CreditNoteLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    invoice_line_id = serializers.UUIDField(allow_null=True)
    description = serializers.CharField()
    quantity = serializers.IntegerField(allow_null=True)
    unit_amount = MoneyField(max_digits=19, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    taxes = CreditNoteLineTaxSerializer(many=True, read_only=True)


class CreditNoteTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField(allow_null=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class CreditNoteTaxBreakdownItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class CreditNoteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    invoice_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CreditNoteStatus.choices)
    reason = serializers.ChoiceField(choices=CreditNoteReason.choices)
    number = serializers.CharField(allow_null=True, source="effective_number", read_only=True)
    numbering_system_id = serializers.UUIDField(allow_null=True)
    currency = CurrencyField()
    issue_date = serializers.DateField(allow_null=True)
    metadata = MetadataField()
    description = serializers.CharField(allow_null=True)
    delivery_method = serializers.ChoiceField(choices=CreditNoteDeliveryMethod.choices)
    recipients = serializers.ListField(child=serializers.EmailField(), allow_empty=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True)
    payment_connection_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    issued_at = serializers.DateTimeField(allow_null=True)
    voided_at = serializers.DateTimeField(allow_null=True)
    pdf_id = serializers.UUIDField(allow_null=True)
    customer = CreditNoteCustomerSerializer(source="invoice.customer_on_invoice", read_only=True)
    account = CreditNoteAccountSerializer(source="invoice.account_on_invoice", read_only=True)
    lines = CreditNoteLineSerializer(many=True, read_only=True)
    taxes = CreditNoteTaxSerializer(many=True, read_only=True)
    tax_breakdown = CreditNoteTaxBreakdownItemSerializer(source="taxes.breakdown", many=True, read_only=True)


class CreditNoteCreateSerializer(serializers.Serializer):
    invoice_id = InvoiceRelatedField(source="invoice")
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    reason = serializers.ChoiceField(choices=CreditNoteReason.choices, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False, max_length=500)
    delivery_method = serializers.ChoiceField(choices=CreditNoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_invoice_id(self, value):
        if value.status not in {InvoiceStatus.OPEN, InvoiceStatus.PAID}:
            raise serializers.ValidationError("Invoice must be finalized before creating credit notes")

        if value.outstanding_amount.amount <= 0:
            raise serializers.ValidationError("Invoice has no outstanding balance to credit")

        if value.credit_notes.filter(status=CreditNoteStatus.DRAFT).exists():
            raise serializers.ValidationError("Only one draft credit note is allowed per invoice")

        return value

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == CreditNoteDeliveryMethod.AUTOMATIC and not has_feature(
            account, FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class CreditNoteUpdateSerializer(serializers.Serializer):
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    reason = serializers.ChoiceField(choices=CreditNoteReason.choices, required=False)
    metadata = MetadataField(required=False)
    description = serializers.CharField(allow_null=True, required=False, max_length=500)
    delivery_method = serializers.ChoiceField(choices=CreditNoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == CreditNoteDeliveryMethod.AUTOMATIC and not has_feature(
            account, FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class CreditNoteIssueSerializer(serializers.Serializer):
    issue_date = serializers.DateField(allow_null=True, required=False)


class CreditNoteVoidSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_null=True, required=False, max_length=600)


class CreditNoteLineCreateSerializer(serializers.Serializer):
    credit_note_id = CreditNoteRelatedField(source="credit_note")
    invoice_line_id = InvoiceLineRelatedField(source="invoice_line", allow_null=True, required=False)
    quantity = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)

    def validate(self, data):
        credit_note = data["credit_note"]
        if data.get("unit_amount") is not None:
            data["unit_amount"] = Money(data["unit_amount"], credit_note.currency)

        if data.get("amount") is not None:
            data["amount"] = Money(data["amount"], credit_note.currency)

        invoice_line = data.get("invoice_line")
        if invoice_line is None:
            return self._validate_custom_line(data, credit_note)

        return self._validate_invoice_line(data, credit_note, invoice_line)

    def _validate_custom_line(self, data, credit_note):
        unit_amount = data.get("unit_amount")
        if unit_amount is None:
            # TODO: add test case for this
            raise serializers.ValidationError({"unit_amount": "Unit amount is required for custom credit note lines"})

        quantity = data.get("quantity") or 1
        total_amount = clamp_money(unit_amount * quantity)

        if not credit_note.can_apply_total(new_total=total_amount):
            raise serializers.ValidationError("Credit note amount exceeds the invoice balance")

        data["quantity"] = quantity
        return data

    def _validate_invoice_line(self, data, credit_note, invoice_line):
        if invoice_line.invoice_id != credit_note.invoice_id:
            # TODO: add test case for this
            raise serializers.ValidationError("Invoice line does not belong to the credit note invoice")

        amount = data.get("amount")
        quantity = data.get("quantity")

        if amount is not None and quantity is not None:
            raise serializers.ValidationError("Provide either quantity or amount for invoice lines")

        if invoice_line.outstanding_amount.amount <= 0:
            raise serializers.ValidationError("Invoice line has no outstanding balance to credit")

        if amount is None and quantity is None:
            quantity = invoice_line.outstanding_quantity

        if quantity is not None and invoice_line.quantity and invoice_line.outstanding_quantity < quantity:
            raise serializers.ValidationError({"quantity": "Quantity exceeds the outstanding quantity"})

        amounts = calculate_credit_note_line_amounts(
            invoice_line,
            quantity=quantity,
            amount=amount,
        )
        total_amount = amounts[3]

        ratio = amounts[4]
        if amount is not None and amounts[0] < amount:
            raise serializers.ValidationError({"amount": "Amount exceeds the outstanding amount"})

        if quantity is not None and invoice_line.quantity:
            requested_ratio = Decimal(quantity) / Decimal(invoice_line.quantity)
            if ratio < requested_ratio:
                raise serializers.ValidationError({"quantity": "Quantity exceeds the outstanding quantity"})

        if not credit_note.can_apply_total(new_total=total_amount):
            # TODO: test it
            raise serializers.ValidationError("Credit note amount exceeds the invoice balance")

        data["quantity"] = quantity if amount is None else None
        data["amount"] = amount
        data["calculated_amounts"] = amounts

        return data

    def validate_credit_note_id(self, value):
        if value.status != CreditNoteStatus.DRAFT:
            raise serializers.ValidationError("Cannot modify issued credit note")
        return value


class CreditNoteLineUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, allow_null=True, required=False)

    def validate(self, data):
        if self.instance.invoice_line_id is None and data.get("amount") is not None:
            raise serializers.ValidationError({"amount": "Amount can only be set for invoice lines"})

        if self.instance.invoice_line_id:
            return self._validate_invoice_line(self.instance, data)

        return self._validate_custom_line(self.instance, data)

    def _validate_custom_line(self, line, data):
        quantity = data.get("quantity") or line.quantity
        unit_amount = data.get("unit_amount") or line.unit_amount
        total_amount = clamp_money(unit_amount * quantity)

        if not line.credit_note.can_apply_total(new_total=total_amount, exclude_line=line):
            raise serializers.ValidationError("Credit note amount exceeds the invoice balance")

        data["quantity"] = quantity
        return data

    def _validate_invoice_line(self, line, data):
        invoice_line = line.invoice_line
        amount = data.get("amount")
        quantity = data.get("quantity")

        if amount is not None and quantity is not None:
            raise serializers.ValidationError("Provide either quantity or amount for invoice lines")

        if amount is None and quantity is None:
            quantity = line.quantity

        amounts = calculate_credit_note_line_amounts(
            invoice_line,
            quantity=quantity,
            amount=amount,
        )
        total_amount = amounts[3]

        if not line.credit_note.can_apply_total(new_total=total_amount, exclude_line=line):
            # TODO: test it
            raise serializers.ValidationError("Credit note amount exceeds the invoice balance")

        ratio = amounts[4]
        if amount is not None and amounts[0] < amount:
            raise serializers.ValidationError({"amount": "Amount exceeds the outstanding amount"})

        if quantity is not None and invoice_line.quantity:
            requested_ratio = Decimal(quantity) / Decimal(invoice_line.quantity)
            if ratio < requested_ratio:
                raise serializers.ValidationError({"quantity": "Quantity exceeds the outstanding quantity"})

        data["quantity"] = quantity if amount is None else None
        data["amount"] = amount
        data["calculated_amounts"] = amounts
        return data

    def validate_unit_amount(self, value):
        return Money(value, self.instance.currency)

    def validate_amount(self, value):
        return Money(value, self.instance.currency)


class CreditNoteLineTaxCreateSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")
