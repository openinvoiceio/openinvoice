from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from apps.addresses.serializers import AddressSerializer
from apps.coupons.fields import CouponRelatedField
from apps.coupons.serializers import CouponSerializer
from apps.customers.fields import CustomerRelatedField
from apps.integrations.enums import PaymentProvider
from apps.integrations.fields import IntegrationConnectionField
from apps.numbering_systems.enums import NumberingSystemAppliesTo
from apps.numbering_systems.fields import NumberingSystemRelatedField
from apps.prices.fields import PriceRelatedField
from apps.prices.validators import PriceIsActive, PriceProductIsActive
from apps.taxes.fields import TaxRateRelatedField
from common.access import has_feature
from common.enums import FeatureCode
from common.fields import CurrencyField, MetadataField
from common.validators import AllOrNoneValidator, ExactlyOneValidator

from .enums import InvoiceDeliveryMethod, InvoiceStatus
from .fields import InvoiceRelatedField


class InvoiceCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="customer.id")
    name = serializers.CharField(source="effective_customer.name")
    legal_name = serializers.CharField(allow_null=True, source="effective_customer.legal_name")
    legal_number = serializers.CharField(allow_null=True, source="effective_customer.legal_number")
    email = serializers.CharField(allow_null=True, source="effective_customer.email")
    phone = serializers.CharField(allow_null=True, source="effective_customer.phone")
    description = serializers.CharField(allow_null=True, source="effective_customer.description")
    billing_address = AddressSerializer(source="effective_customer.billing_address")
    shipping_address = AddressSerializer(source="effective_customer.shipping_address")
    logo_id = serializers.UUIDField(allow_null=True, source="effective_customer.logo_id")


class InvoiceAccountSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="account.id")
    name = serializers.CharField(source="effective_account.name")
    legal_name = serializers.CharField(allow_null=True, source="effective_account.legal_name")
    legal_number = serializers.CharField(allow_null=True, source="effective_account.legal_number")
    email = serializers.CharField(allow_null=True, source="effective_account.email")
    phone = serializers.CharField(allow_null=True, source="effective_account.phone")
    address = AddressSerializer(source="effective_account.address")
    logo_id = serializers.UUIDField(allow_null=True, source="effective_account.logo_id")


class InvoiceLineDiscountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    coupon = CouponSerializer(read_only=True)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceDiscountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    coupon = CouponSerializer(read_only=True)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceDiscountBreakdownItemSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True)
    amount = MoneyField(max_digits=19, decimal_places=2)
    coupon_id = serializers.UUIDField()


class InvoiceLineTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceTaxBreakdownItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2)
    price_id = serializers.UUIDField(allow_null=True)
    product_id = serializers.UUIDField(source="price.product_id", allow_null=True)
    amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    credit_quantity = serializers.IntegerField(read_only=True)
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    outstanding_quantity = serializers.IntegerField(read_only=True)
    discounts = InvoiceLineDiscountSerializer(many=True)
    taxes = InvoiceLineTaxSerializer(many=True)


class InvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=InvoiceStatus.choices)
    number = serializers.CharField(allow_null=True, source="effective_number", read_only=True)
    numbering_system_id = serializers.UUIDField(allow_null=True)
    previous_revision_id = serializers.UUIDField(allow_null=True)
    latest_revision_id = serializers.UUIDField(allow_null=True)
    currency = CurrencyField()
    issue_date = serializers.DateField(allow_null=True)
    sell_date = serializers.DateField(allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    net_payment_term = serializers.IntegerField()
    delivery_method = serializers.ChoiceField(choices=InvoiceDeliveryMethod.choices)
    recipients = serializers.ListField(child=serializers.EmailField(), allow_empty=True)
    customer = InvoiceCustomerSerializer(source="*", read_only=True)
    account = InvoiceAccountSerializer(source="*", read_only=True)
    metadata = MetadataField()
    custom_fields = MetadataField()
    footer = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2)
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2)
    total_paid_amount = MoneyField(max_digits=19, decimal_places=2)
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True)
    payment_connection_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    opened_at = serializers.DateTimeField(allow_null=True)
    paid_at = serializers.DateTimeField(allow_null=True)
    voided_at = serializers.DateTimeField(allow_null=True)
    pdf_id = serializers.UUIDField(allow_null=True)
    lines = InvoiceLineSerializer(many=True)
    discounts = InvoiceDiscountSerializer(many=True, source="discounts.for_invoice", read_only=True)
    taxes = InvoiceTaxSerializer(many=True, source="taxes.for_invoice", read_only=True)
    discount_breakdown = InvoiceDiscountBreakdownItemSerializer(many=True, source="discounts.breakdown", read_only=True)
    tax_breakdown = InvoiceTaxBreakdownItemSerializer(many=True, source="taxes.breakdown", read_only=True)


class InvoiceCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    previous_revision_id = InvoiceRelatedField(source="previous_revision", required=False)
    currency = CurrencyField(allow_null=True, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    sell_date = serializers.DateField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    custom_fields = MetadataField(allow_null=True, required=False)
    footer = serializers.CharField(allow_null=True, required=False, max_length=600)
    description = serializers.CharField(allow_null=True, required=False, max_length=600)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True, required=False)
    payment_connection_id = IntegrationConnectionField(
        source="payment_connection", type_field="payment_provider", allow_null=True, required=False
    )
    delivery_method = serializers.ChoiceField(choices=InvoiceDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    class Meta:
        validators = [
            ExactlyOneValidator("customer", "previous_revision"),
            AllOrNoneValidator("payment_provider", "payment_connection"),
        ]

    def validate_previous_revision_id(self, value):
        if value.status != InvoiceStatus.OPEN:
            raise serializers.ValidationError("Only open invoices can be revised")

        if value.revisions.exclude(status=InvoiceStatus.VOIDED).exists():
            raise serializers.ValidationError("Invoice already has a subsequent revision")

        if value.latest_revision_id != value.id:
            raise serializers.ValidationError("Only the latest revision can be revised")

        return value

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == InvoiceDeliveryMethod.AUTOMATIC and not has_feature(
            account, FeatureCode.AUTOMATIC_INVOICE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class InvoiceUpdateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer", required=False)
    number = serializers.CharField(max_length=255, allow_null=True, required=False)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    currency = CurrencyField(required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    sell_date = serializers.DateField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(required=False)
    metadata = MetadataField(required=False)
    custom_fields = MetadataField(required=False)
    footer = serializers.CharField(max_length=600, allow_null=True, required=False)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True, required=False)
    payment_connection_id = IntegrationConnectionField(
        source="payment_connection", type_field="payment_provider", allow_null=True, required=False
    )
    delivery_method = serializers.ChoiceField(choices=InvoiceDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    class Meta:
        validators = [
            AllOrNoneValidator("payment_provider", "payment_connection"),
        ]

    def validate_customer_id(self, value):
        if self.instance.previous_revision and self.instance.customer_id != value.id:
            raise serializers.ValidationError("Revision must use the same customer")

        return value

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == InvoiceDeliveryMethod.AUTOMATIC and not has_feature(
            account, FeatureCode.AUTOMATIC_INVOICE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class InvoiceLineCreateSerializer(serializers.Serializer):
    invoice_id = InvoiceRelatedField(source="invoice")
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    class Meta:
        validators = [
            ExactlyOneValidator("unit_amount", "price"),
        ]

    def validate(self, data):
        invoice = data["invoice"]
        unit_amount = data.get("unit_amount")
        price = data.get("price")

        if invoice.status != InvoiceStatus.DRAFT:
            raise serializers.ValidationError("Only draft invoices can be modified")

        if price and invoice.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match invoice currency")

        if unit_amount:
            data["unit_amount"] = Money(unit_amount, invoice.currency)

        return data


class InvoiceLineUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    class Meta:
        validators = [
            ExactlyOneValidator("unit_amount", "price"),
        ]

    def validate_price_id(self, value):
        if self.instance.currency != value.currency:
            raise serializers.ValidationError("Price currency does not match invoice currency")

        return value

    def validate_unit_amount(self, value):
        return Money(value, self.instance.currency)


class InvoiceLineDiscountCreateSerializer(serializers.Serializer):
    coupon_id = CouponRelatedField(source="coupon")

    def validate_coupon_id(self, value):
        invoice_line = self.context["invoice_line"]

        if invoice_line.currency != value.currency:
            raise serializers.ValidationError("Coupon currency mismatch")

        if invoice_line.discounts.filter(coupon_id=value.id).exists():
            raise serializers.ValidationError("Given coupon is already applied to this invoice line")

        return value


class InvoiceDiscountCreateSerializer(serializers.Serializer):
    coupon_id = CouponRelatedField(source="coupon")

    def validate_coupon_id(self, value):
        invoice = self.context["invoice"]

        if invoice.currency != value.currency:
            raise serializers.ValidationError("Coupon currency mismatch")

        if invoice.discounts.filter(coupon_id=value.id).exists():
            raise serializers.ValidationError("Given coupon is already applied to this invoice")

        return value


class InvoiceLineTaxCreateSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")

    def validate_tax_rate_id(self, value):
        invoice_line = self.context["invoice_line"]

        if invoice_line.taxes.filter(tax_rate_id=value.id).exists():
            raise serializers.ValidationError("Given tax rate is already applied to this invoice line")

        return value


class InvoiceTaxCreateSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")

    def validate_tax_rate_id(self, value):
        invoice = self.context["invoice"]

        if invoice.taxes.filter(tax_rate_id=value.id).exists():
            raise serializers.ValidationError("Given tax rate is already applied to this invoice")

        return value
