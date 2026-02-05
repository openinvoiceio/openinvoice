from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from openinvoice.accounts.fields import BusinessProfileRelatedField
from openinvoice.accounts.serializers import BusinessProfileSerializer
from openinvoice.core.access import has_feature
from openinvoice.core.choices import FeatureCode
from openinvoice.core.fields import CurrencyField, MetadataField
from openinvoice.core.validators import ExactlyOneValidator
from openinvoice.coupons.fields import CouponRelatedField
from openinvoice.coupons.serializers import CouponSerializer
from openinvoice.customers.fields import BillingProfileRelatedField, CustomerRelatedField
from openinvoice.customers.serializers import BillingProfileSerializer
from openinvoice.numbering_systems.choices import NumberingSystemAppliesTo
from openinvoice.numbering_systems.fields import NumberingSystemRelatedField
from openinvoice.prices.fields import PriceRelatedField
from openinvoice.prices.validators import PriceIsActive, PriceProductIsActive
from openinvoice.tax_rates.fields import TaxRateRelatedField

from .choices import QuoteDeliveryMethod, QuotePreviewFormat, QuoteStatus
from .fields import QuoteRelatedField


class QuoteLineDiscountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    coupon = CouponSerializer(read_only=True)
    amount = MoneyField(max_digits=19, decimal_places=2)


class QuoteLineTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class QuoteDiscountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    coupon = CouponSerializer(read_only=True)
    amount = MoneyField(max_digits=19, decimal_places=2)


class QuoteTaxSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tax_rate_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = MoneyField(max_digits=19, decimal_places=2)


class QuoteLineSerializer(serializers.Serializer):
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
    discounts = QuoteLineDiscountSerializer(many=True)
    taxes = QuoteLineTaxSerializer(many=True)


class QuoteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=QuoteStatus.choices)
    number = serializers.CharField(allow_null=True, source="effective_number", read_only=True)
    numbering_system_id = serializers.UUIDField(allow_null=True)
    currency = CurrencyField()
    issue_date = serializers.DateField(allow_null=True)
    billing_profile = BillingProfileSerializer(read_only=True)
    business_profile = BusinessProfileSerializer(read_only=True)
    metadata = MetadataField()
    custom_fields = MetadataField()
    footer = serializers.CharField(allow_null=True)
    delivery_method = serializers.ChoiceField(choices=QuoteDeliveryMethod.choices)
    recipients = serializers.ListField(child=serializers.EmailField(), allow_empty=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2)
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2)
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    opened_at = serializers.DateTimeField(allow_null=True)
    accepted_at = serializers.DateTimeField(allow_null=True)
    canceled_at = serializers.DateTimeField(allow_null=True)
    pdf_id = serializers.UUIDField(allow_null=True)
    invoice_id = serializers.UUIDField(allow_null=True)
    lines = QuoteLineSerializer(many=True)
    discounts = QuoteDiscountSerializer(many=True, source="discounts.for_quote", read_only=True)
    taxes = QuoteTaxSerializer(many=True, source="taxes.for_quote", read_only=True)


class QuoteCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer")
    billing_profile_id = BillingProfileRelatedField(source="billing_profile", required=False)
    business_profile_id = BusinessProfileRelatedField(source="business_profile", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.QUOTE, allow_null=True, required=False
    )
    currency = CurrencyField(allow_null=True, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    custom_fields = MetadataField(allow_null=True, required=False)
    footer = serializers.CharField(allow_null=True, required=False, max_length=600)
    delivery_method = serializers.ChoiceField(choices=QuoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == QuoteDeliveryMethod.AUTOMATIC and not has_feature(account, FeatureCode.AUTOMATIC_QUOTE_DELIVERY):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class QuoteUpdateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer", required=False)
    billing_profile_id = BillingProfileRelatedField(source="billing_profile", required=False)
    business_profile_id = BusinessProfileRelatedField(source="business_profile", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.QUOTE, allow_null=True, required=False
    )
    currency = CurrencyField(required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    custom_fields = MetadataField(allow_null=True, required=False)
    footer = serializers.CharField(allow_null=True, required=False, max_length=600)
    delivery_method = serializers.ChoiceField(choices=QuoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == QuoteDeliveryMethod.AUTOMATIC and not has_feature(account, FeatureCode.AUTOMATIC_QUOTE_DELIVERY):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class QuoteLineCreateSerializer(serializers.Serializer):
    quote_id = QuoteRelatedField(source="quote")
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    class Meta:
        validators = [
            ExactlyOneValidator("unit_amount", "price"),
        ]

    def validate(self, data):
        quote = data["quote"]
        unit_amount = data.get("unit_amount")
        price = data.get("price")

        if quote.status != QuoteStatus.DRAFT:
            raise serializers.ValidationError("Only draft quotes can be modified")

        if price and quote.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match quote currency")

        if unit_amount is not None and not isinstance(unit_amount, Money):
            data["unit_amount"] = Money(unit_amount, quote.currency)

        return data


class QuoteLineUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    class Meta:
        validators = [
            ExactlyOneValidator("unit_amount", "price"),
        ]

    def validate(self, data):
        price = data.get("price")

        if price and self.instance.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match quote currency")

        return data

    def validate_unit_amount(self, value):
        return Money(value, self.instance.currency)


class QuoteLineDiscountCreateSerializer(serializers.Serializer):
    coupon_id = CouponRelatedField(source="coupon")

    def validate_coupon_id(self, value):
        quote_line = self.context["quote_line"]

        if quote_line.currency != value.currency:
            raise serializers.ValidationError("Coupon currency mismatch")

        if quote_line.discounts.filter(coupon_id=value.id).exists():
            raise serializers.ValidationError("Given coupon is already applied to this quote line")

        return value


class QuoteDiscountCreateSerializer(serializers.Serializer):
    coupon_id = CouponRelatedField(source="coupon")

    def validate_coupon_id(self, value):
        quote = self.context["quote"]

        if quote.currency != value.currency:
            raise serializers.ValidationError("Coupon currency mismatch")

        if quote.discounts.filter(coupon_id=value.id).exists():
            raise serializers.ValidationError("Given coupon is already applied to this quote")

        return value


class QuoteLineTaxCreateSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")

    def validate_tax_rate_id(self, value):
        quote_line = self.context["quote_line"]

        if quote_line.taxes.filter(tax_rate_id=value.id).exists():
            raise serializers.ValidationError("Given tax rate is already applied to this quote line")

        return value


class QuoteTaxCreateSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")

    def validate_tax_rate_id(self, value):
        quote = self.context["quote"]

        if quote.taxes.filter(tax_rate_id=value.id).exists():
            raise serializers.ValidationError("Given tax rate is already applied to this quote")

        return value


class QuotePreviewSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=QuotePreviewFormat.choices, default=QuotePreviewFormat.PDF)
