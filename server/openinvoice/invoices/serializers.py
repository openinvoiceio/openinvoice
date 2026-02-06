from djmoney.contrib.django_rest_framework.fields import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from openinvoice.accounts.fields import BusinessProfileRelatedField
from openinvoice.accounts.serializers import BusinessProfileSerializer
from openinvoice.core.fields import CurrencyField, LanguageField, MetadataField
from openinvoice.core.validators import AllOrNoneValidator, AtMostOneValidator
from openinvoice.coupons.fields import CouponRelatedField
from openinvoice.coupons.serializers import CouponSerializer
from openinvoice.customers.fields import BillingProfileRelatedField, CustomerRelatedField, ShippingProfileRelatedField
from openinvoice.customers.serializers import BillingProfileSerializer, ShippingProfileSerializer
from openinvoice.integrations.choices import PaymentProvider
from openinvoice.integrations.fields import IntegrationConnectionField
from openinvoice.numbering_systems.choices import NumberingSystemAppliesTo
from openinvoice.numbering_systems.fields import NumberingSystemRelatedField
from openinvoice.prices.fields import PriceRelatedField
from openinvoice.prices.validators import PriceIsActive, PriceProductIsActive
from openinvoice.shipping_rates.fields import ShippingRateRelatedField
from openinvoice.tax_rates.fields import TaxRateRelatedField
from openinvoice.tax_rates.serializers import TaxRateSerializer

from .choices import InvoiceDeliveryMethod, InvoiceDocumentAudience, InvoiceStatus, InvoiceTaxBehavior
from .fields import InvoiceRelatedField
from .validators import (
    AutomaticDeliveryMethodValidator,
    MaxCouponsValidator,
    MaxTaxRatesValidator,
    validate_coupons_currency,
)


class InvoiceDiscountSerializer(serializers.Serializer):
    coupon_id = serializers.UUIDField()
    name = serializers.CharField()
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceTaxSerializer(serializers.Serializer):
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class InvoiceShippingSerializer(serializers.Serializer):
    profile = ShippingProfileSerializer(allow_null=True)
    amount = MoneyField(max_digits=19, decimal_places=2)
    total_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    shipping_rate_id = serializers.UUIDField(allow_null=True)
    tax_rates = TaxRateSerializer(many=True)
    total_taxes = InvoiceTaxSerializer(many=True)


class InvoiceLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2)
    price_id = serializers.UUIDField(allow_null=True)
    product_id = serializers.UUIDField(source="price.product_id", allow_null=True)
    amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    credit_quantity = serializers.IntegerField(read_only=True)
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2, read_only=True)
    outstanding_quantity = serializers.IntegerField(read_only=True)
    coupons = CouponSerializer(many=True)
    discounts = InvoiceDiscountSerializer(many=True)
    total_discounts = InvoiceDiscountSerializer(many=True)
    tax_rates = TaxRateSerializer(many=True)
    taxes = InvoiceTaxSerializer(many=True)
    total_taxes = InvoiceTaxSerializer(many=True)


class InvoiceDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    audience = serializers.ListField(child=serializers.ChoiceField(choices=InvoiceDocumentAudience.choices))
    language = LanguageField()
    footer = serializers.CharField(allow_null=True)
    memo = serializers.CharField(allow_null=True)
    custom_fields = MetadataField()
    url = serializers.URLField(source="file.data.url", allow_null=True, read_only=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class InvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=InvoiceStatus.choices)
    number = serializers.CharField(allow_null=True, source="effective_number", read_only=True)
    numbering_system_id = serializers.UUIDField(allow_null=True)
    currency = CurrencyField()
    tax_behavior = serializers.ChoiceField(choices=InvoiceTaxBehavior.choices)
    issue_date = serializers.DateField(allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    net_payment_term = serializers.IntegerField(min_value=0)
    delivery_method = serializers.ChoiceField(choices=InvoiceDeliveryMethod.choices)
    recipients = serializers.ListField(child=serializers.EmailField(), allow_empty=True)
    billing_profile = BillingProfileSerializer(read_only=True)
    business_profile = BusinessProfileSerializer(read_only=True)
    metadata = MetadataField()
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2)
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2)
    total_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    shipping_amount = MoneyField(max_digits=19, decimal_places=2)
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
    previous_revision_id = serializers.UUIDField(allow_null=True)
    lines = InvoiceLineSerializer(many=True)
    documents = InvoiceDocumentSerializer(many=True)
    shipping = InvoiceShippingSerializer()
    coupons = CouponSerializer(many=True)
    discounts = InvoiceDiscountSerializer(many=True)
    total_discounts = InvoiceDiscountSerializer(many=True)
    tax_rates = TaxRateSerializer(many=True)
    taxes = InvoiceTaxSerializer(many=True)
    total_taxes = InvoiceTaxSerializer(many=True)


class InvoiceShippingAddSerializer(serializers.Serializer):
    shipping_rate_id = ShippingRateRelatedField(source="shipping_rate")
    shipping_profile_id = ShippingProfileRelatedField(source="profile", required=False, allow_null=True)
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])


class InvoiceCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer")
    billing_profile_id = BillingProfileRelatedField(source="billing_profile", required=False)
    business_profile_id = BusinessProfileRelatedField(source="business_profile", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    currency = CurrencyField(allow_null=True, required=False)
    tax_behavior = serializers.ChoiceField(choices=InvoiceTaxBehavior.choices, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True, required=False)
    payment_connection_id = IntegrationConnectionField(
        source="payment_connection", type_field="payment_provider", allow_null=True, required=False
    )
    delivery_method = serializers.ChoiceField(
        choices=InvoiceDeliveryMethod.choices,
        required=False,
        validators=[
            AutomaticDeliveryMethodValidator(),
        ],
    )
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])
    coupons = CouponRelatedField(many=True, required=False, validators=[MaxCouponsValidator()])
    shipping = InvoiceShippingAddSerializer(required=False, allow_null=True)

    def validate(self, data):
        customer = data["customer"]
        billing_profile = data.get("billing_profile") or customer.default_billing_profile
        currency = data.get("currency") or billing_profile.currency or customer.account.default_currency

        if data.get("coupons"):
            validate_coupons_currency(data["coupons"], currency)

        return data

    class Meta:
        validators = [
            AllOrNoneValidator("payment_provider", "payment_connection"),
        ]


class InvoiceRevisionCreateSerializer(serializers.Serializer):
    billing_profile_id = BillingProfileRelatedField(source="billing_profile", required=False)
    business_profile_id = BusinessProfileRelatedField(source="business_profile", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    currency = CurrencyField(allow_null=True, required=False)
    tax_behavior = serializers.ChoiceField(choices=InvoiceTaxBehavior.choices, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True, required=False)
    payment_connection_id = IntegrationConnectionField(
        source="payment_connection", type_field="payment_provider", allow_null=True, required=False
    )
    delivery_method = serializers.ChoiceField(
        choices=InvoiceDeliveryMethod.choices,
        required=False,
        validators=[AutomaticDeliveryMethodValidator()],
    )
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])
    coupons = CouponRelatedField(many=True, required=False, validators=[MaxCouponsValidator()])
    shipping = InvoiceShippingAddSerializer(required=False, allow_null=True)

    class Meta:
        validators = [
            AllOrNoneValidator("payment_provider", "payment_connection"),
        ]

    def validate(self, data):
        currency = data.get("currency") or self.instance.currency

        if data.get("coupons"):
            validate_coupons_currency(data["coupons"], currency)

        return data


class InvoiceUpdateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer", required=False)
    billing_profile_id = BillingProfileRelatedField(source="billing_profile", required=False)
    business_profile_id = BusinessProfileRelatedField(source="business_profile", required=False)
    number = serializers.CharField(max_length=255, allow_null=True, required=False)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    currency = CurrencyField(required=False)
    tax_behavior = serializers.ChoiceField(choices=InvoiceTaxBehavior.choices, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(min_value=0, required=False)
    metadata = MetadataField(required=False)
    payment_provider = serializers.ChoiceField(choices=PaymentProvider.choices, allow_null=True, required=False)
    payment_connection_id = IntegrationConnectionField(
        source="payment_connection", type_field="payment_provider", allow_null=True, required=False
    )
    delivery_method = serializers.ChoiceField(
        choices=InvoiceDeliveryMethod.choices,
        required=False,
        validators=[AutomaticDeliveryMethodValidator()],
    )
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])
    coupons = CouponRelatedField(many=True, required=False, validators=[MaxCouponsValidator()])
    shipping = InvoiceShippingAddSerializer(required=False, allow_null=True)

    class Meta:
        validators = [
            AllOrNoneValidator("payment_provider", "payment_connection"),
        ]

    def validate(self, data):
        currency = data.get("currency") or self.instance.currency

        if data.get("coupons"):
            validate_coupons_currency(data["coupons"], currency)

        return data

    def validate_customer_id(self, value):
        if self.instance.previous_revision and self.instance.customer_id != value.id:
            raise serializers.ValidationError("Revision must use the same customer")

        return value


class InvoiceDocumentCreateSerializer(serializers.Serializer):
    audience = serializers.ListField(
        child=serializers.ChoiceField(choices=InvoiceDocumentAudience.choices),
        required=False,
        allow_empty=True,
    )
    language = LanguageField()
    footer = serializers.CharField(allow_null=True, required=False)
    memo = serializers.CharField(allow_null=True, required=False)
    custom_fields = MetadataField(required=False)


class InvoiceDocumentUpdateSerializer(serializers.Serializer):
    audience = serializers.ListField(
        child=serializers.ChoiceField(choices=InvoiceDocumentAudience.choices),
        required=False,
        allow_empty=True,
    )
    language = LanguageField(required=False)
    footer = serializers.CharField(allow_null=True, required=False)
    memo = serializers.CharField(allow_null=True, required=False)
    custom_fields = MetadataField(required=False)


class InvoiceLineCreateSerializer(serializers.Serializer):
    invoice_id = InvoiceRelatedField(source="invoice")
    description = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")
    quantity = serializers.IntegerField(required=False, default=1)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])
    coupons = CouponRelatedField(many=True, required=False, validators=[MaxCouponsValidator()])

    class Meta:
        validators = [
            AtMostOneValidator("unit_amount", "price"),
        ]

    def validate(self, data):
        invoice = data["invoice"]
        unit_amount = data.get("unit_amount")
        price = data.get("price")

        if invoice.status != InvoiceStatus.DRAFT:
            raise serializers.ValidationError("Only draft invoices can be modified")

        if price and invoice.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match invoice currency")

        if data.get("coupons"):
            validate_coupons_currency(data["coupons"], invoice.currency)

        if price is None and unit_amount is None:
            data["unit_amount"] = Money(0, invoice.currency)
        elif unit_amount is not None:
            data["unit_amount"] = Money(unit_amount, invoice.currency)

        return data


class InvoiceLineUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)
    quantity = serializers.IntegerField(required=False)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])
    tax_rates = TaxRateRelatedField(many=True, required=False, validators=[MaxTaxRatesValidator()])
    coupons = CouponRelatedField(many=True, required=False, validators=[MaxCouponsValidator()])

    def validate(self, data):
        if data.get("coupons"):
            validate_coupons_currency(data["coupons"], self.instance.currency)

        if "price" in data and self.instance.price is None:
            raise serializers.ValidationError("Cannot change pricing method")

        if "unit_amount" in data and self.instance.price is not None:
            raise serializers.ValidationError("Cannot change pricing method")

        return data

    def validate_price_id(self, value):
        if self.instance.currency != value.currency:
            raise serializers.ValidationError("Price currency does not match invoice currency")

        return value

    def validate_unit_amount(self, value):
        return Money(value, self.instance.currency)
