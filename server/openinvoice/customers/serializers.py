from rest_framework import serializers

from openinvoice.addresses.serializers import AddressSerializer
from openinvoice.core.fields import CurrencyField, LanguageField, MetadataField
from openinvoice.files.fields import FileRelatedField
from openinvoice.numbering_systems.choices import NumberingSystemAppliesTo
from openinvoice.numbering_systems.fields import NumberingSystemRelatedField
from openinvoice.tax_ids.serializers import TaxIdSerializer
from openinvoice.tax_rates.fields import TaxRateRelatedField
from openinvoice.tax_rates.serializers import TaxRateSerializer

from .fields import CustomerRelatedField


class BillingProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    currency = CurrencyField(allow_null=True)
    language = LanguageField(allow_null=True)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0)
    invoice_numbering_system_id = serializers.UUIDField(allow_null=True)
    credit_note_numbering_system_id = serializers.UUIDField(allow_null=True)
    tax_rates = TaxRateSerializer(many=True, read_only=True)
    tax_ids = TaxIdSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class BillingProfileCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer")
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, allow_null=True, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    language = LanguageField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0, required=False)
    invoice_numbering_system_id = NumberingSystemRelatedField(
        source="invoice_numbering_system",
        applies_to=NumberingSystemAppliesTo.INVOICE,
        allow_null=True,
        required=False,
    )
    credit_note_numbering_system_id = NumberingSystemRelatedField(
        source="credit_note_numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    tax_rates = TaxRateRelatedField(many=True, required=False)


class CustomerBillingProfileCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, allow_null=True, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    language = LanguageField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0, required=False)
    invoice_numbering_system_id = NumberingSystemRelatedField(
        source="invoice_numbering_system",
        applies_to=NumberingSystemAppliesTo.INVOICE,
        allow_null=True,
        required=False,
    )
    credit_note_numbering_system_id = NumberingSystemRelatedField(
        source="credit_note_numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    tax_rates = TaxRateRelatedField(many=True, required=False)


class BillingProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, allow_null=True, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    language = LanguageField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, min_value=0, required=False)
    invoice_numbering_system_id = NumberingSystemRelatedField(
        source="invoice_numbering_system",
        applies_to=NumberingSystemAppliesTo.INVOICE,
        allow_null=True,
        required=False,
    )
    credit_note_numbering_system_id = NumberingSystemRelatedField(
        source="credit_note_numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    tax_rates = TaxRateRelatedField(many=True, required=False)


class ShippingProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class ShippingProfileCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer")
    name = serializers.CharField(allow_null=True, required=False)
    phone = serializers.CharField(allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)


class CustomerShippingProfileCreateSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, required=False)
    phone = serializers.CharField(allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)


class ShippingProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, required=False)
    phone = serializers.CharField(allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)


class CustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    description = serializers.CharField(allow_null=True)
    metadata = MetadataField()
    default_billing_profile = BillingProfileSerializer()
    default_shipping_profile = ShippingProfileSerializer(allow_null=True)
    logo_id = serializers.UUIDField(allow_null=True)
    logo_url = serializers.FileField(allow_null=True, use_url=True, source="logo.data")
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class CustomerCreateSerializer(serializers.Serializer):
    billing_profile = CustomerBillingProfileCreateSerializer()
    shipping_profile = CustomerShippingProfileCreateSerializer(allow_null=True, required=False)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    metadata = MetadataField(required=False)
    logo_id = FileRelatedField(source="logo", allow_null=True, required=False)


class CustomerUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    metadata = MetadataField(required=False)
    logo_id = FileRelatedField(source="logo", allow_null=True, required=False)


class CustomerTaxRateAssignSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")
