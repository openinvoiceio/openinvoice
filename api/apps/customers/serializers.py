from rest_framework import serializers

from apps.addresses.serializers import AddressSerializer
from apps.files.fields import FileRelatedField
from apps.numbering_systems.choices import NumberingSystemAppliesTo
from apps.numbering_systems.fields import NumberingSystemRelatedField
from apps.taxes.fields import TaxRateRelatedField
from apps.taxes.serializers import TaxIdSerializer, TaxRateSerializer
from common.fields import CurrencyField, MetadataField


class CustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField()
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    currency = CurrencyField(allow_null=True)
    net_payment_term = serializers.IntegerField(allow_null=True)
    invoice_numbering_system_id = serializers.UUIDField(allow_null=True)
    credit_note_numbering_system_id = serializers.UUIDField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    metadata = MetadataField()
    billing_address = AddressSerializer()
    shipping_address = AddressSerializer()
    tax_rates = TaxRateSerializer(many=True, read_only=True)
    tax_ids = TaxIdSerializer(many=True, read_only=True)
    logo_id = serializers.UUIDField(allow_null=True)
    logo_url = serializers.FileField(allow_null=True, use_url=True, source="logo.data")
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class CustomerCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, allow_null=True, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, required=False)
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
    metadata = MetadataField(required=False)
    billing_address = AddressSerializer(allow_null=True, required=False)
    shipping_address = AddressSerializer(allow_null=True, required=False)
    logo_id = FileRelatedField(source="logo", allow_null=True, required=False)


class CustomerUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, allow_null=True, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    currency = CurrencyField(allow_null=True, required=False)
    net_payment_term = serializers.IntegerField(allow_null=True, required=False)
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
    metadata = MetadataField(required=False)
    billing_address = AddressSerializer(allow_null=True, required=False)
    shipping_address = AddressSerializer(allow_null=True, required=False)
    logo_id = FileRelatedField(source="logo", allow_null=True, required=False)


class CustomerTaxRateAssignSerializer(serializers.Serializer):
    tax_rate_id = TaxRateRelatedField(source="tax_rate")
