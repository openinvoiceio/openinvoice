from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.money import Money
from rest_framework import serializers

from apps.addresses.serializers import AddressSerializer
from apps.coupons.fields import CouponRelatedField
from apps.coupons.serializers import CouponSerializer
from apps.customers.fields import CustomerRelatedField
from apps.numbering_systems.enums import NumberingSystemAppliesTo
from apps.numbering_systems.fields import NumberingSystemRelatedField
from apps.prices.fields import PriceRelatedField
from apps.prices.validators import PriceIsActive, PriceProductIsActive
from apps.taxes.fields import TaxRateRelatedField
from common.entitlements import has_feature
from common.enums import EntitlementCode
from common.fields import CurrencyField, MetadataField

from .enums import QuoteDeliveryMethod, QuotePreviewFormat, QuoteStatus
from .fields import QuoteRelatedField


class QuoteCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="customer_id")
    name = serializers.CharField(source="effective_customer.name")
    legal_name = serializers.CharField(allow_null=True, source="effective_customer.legal_name")
    legal_number = serializers.CharField(allow_null=True, source="effective_customer.legal_number")
    email = serializers.CharField(allow_null=True, source="effective_customer.email")
    phone = serializers.CharField(allow_null=True, source="effective_customer.phone")
    description = serializers.CharField(allow_null=True, source="effective_customer.description")
    billing_address = AddressSerializer(source="effective_customer.billing_address")
    shipping_address = AddressSerializer(source="effective_customer.shipping_address")
    logo_id = serializers.UUIDField(allow_null=True, source="effective_customer.logo_id")


class QuoteAccountSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="account.id")
    name = serializers.CharField(source="effective_account.name")
    legal_name = serializers.CharField(allow_null=True, source="effective_account.legal_name")
    legal_number = serializers.CharField(allow_null=True, source="effective_account.legal_number")
    email = serializers.CharField(allow_null=True, source="effective_account.email")
    phone = serializers.CharField(allow_null=True, source="effective_account.phone")
    address = AddressSerializer(source="effective_account.address")
    logo_id = serializers.UUIDField(allow_null=True, source="effective_account.logo_id")


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
    customer = QuoteCustomerSerializer(source="*", read_only=True)
    account = QuoteAccountSerializer(source="*", read_only=True)
    metadata = MetadataField()
    custom_fields = MetadataField()
    footer = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
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
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.QUOTE, allow_null=True, required=False
    )
    currency = CurrencyField(allow_null=True, required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    custom_fields = MetadataField(allow_null=True, required=False)
    footer = serializers.CharField(allow_null=True, required=False, max_length=600)
    description = serializers.CharField(allow_null=True, required=False, max_length=600)
    delivery_method = serializers.ChoiceField(choices=QuoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == QuoteDeliveryMethod.AUTOMATIC and not has_feature(
            account, EntitlementCode.AUTOMATIC_QUOTE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class QuoteUpdateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer", required=False)
    number = serializers.CharField(allow_null=True, required=False, max_length=255)
    numbering_system_id = NumberingSystemRelatedField(
        source="numbering_system", applies_to=NumberingSystemAppliesTo.QUOTE, allow_null=True, required=False
    )
    currency = CurrencyField(required=False)
    issue_date = serializers.DateField(allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    custom_fields = MetadataField(allow_null=True, required=False)
    footer = serializers.CharField(allow_null=True, required=False, max_length=600)
    description = serializers.CharField(allow_null=True, required=False, max_length=600)
    delivery_method = serializers.ChoiceField(choices=QuoteDeliveryMethod.choices, required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=True)

    def validate_delivery_method(self, value):
        account = self.context["request"].account

        if value == QuoteDeliveryMethod.AUTOMATIC and not has_feature(
            account, EntitlementCode.AUTOMATIC_QUOTE_DELIVERY
        ):
            raise serializers.ValidationError("Automatic delivery is forbidden for your account.")

        return value


class QuoteLineCreateSerializer(serializers.Serializer):
    quote_id = QuoteRelatedField(source="quote")
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    def validate(self, data):
        quote = data["quote"]
        unit_amount = data.get("unit_amount")
        price = data.get("price")

        if quote.status != QuoteStatus.DRAFT:
            raise serializers.ValidationError("Only draft quotes can be modified")

        if price and quote.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match quote currency")

        if unit_amount is None and price is None:
            raise serializers.ValidationError("Price or unit amount is required")

        if unit_amount is not None and price is not None:
            raise serializers.ValidationError("Price and unit amount are mutually exclusive")

        if unit_amount is not None and not isinstance(unit_amount, Money):
            data["unit_amount"] = Money(unit_amount, quote.currency)

        return data


class QuoteLineUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, allow_blank=True)
    quantity = serializers.IntegerField()
    unit_amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    price_id = PriceRelatedField(source="price", required=False, validators=[PriceIsActive(), PriceProductIsActive()])

    def validate(self, data):
        unit_amount = data.get("unit_amount")
        price = data.get("price")

        if price and self.instance.currency != price.currency:
            raise serializers.ValidationError("Price currency does not match quote currency")

        # TODO: we probably will need to refine this behavior?
        #  Should we allow for changing from price line to unit amount line and vice versa?
        if unit_amount is None and price is None:
            raise serializers.ValidationError("Price or unit amount is required")

        if unit_amount is not None and price is not None:
            raise serializers.ValidationError("Price and unit amount are mutually exclusive")

        if unit_amount is not None and not isinstance(unit_amount, Money):
            data["unit_amount"] = Money(unit_amount, self.instance.currency)

        return data


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
