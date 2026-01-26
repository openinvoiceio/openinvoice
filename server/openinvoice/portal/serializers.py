from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers

from common.fields import CurrencyField
from openinvoice.addresses.serializers import AddressSerializer
from openinvoice.customers.fields import CustomerRelatedField
from openinvoice.invoices.choices import InvoiceStatus
from openinvoice.tax_ids.serializers import TaxIdSerializer


class PortalInvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    number = serializers.CharField(allow_null=True)
    status = serializers.ChoiceField(choices=InvoiceStatus.choices)
    currency = CurrencyField()
    issue_date = serializers.DateField(allow_null=True)
    due_date = serializers.DateField()
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    pdf_url = serializers.URLField(source="pdf.data.url", allow_null=True)


class PortalSessionCreateSerializer(serializers.Serializer):
    customer_id = CustomerRelatedField(source="customer")


class PortalSessionSerializer(serializers.Serializer):
    portal_url = serializers.URLField()


class PortalCustomerShippingSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()


class PortalCustomerShippingUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, required=False)
    phone = serializers.CharField(allow_null=True, required=False)
    address = AddressSerializer(allow_null=True, required=False)


class PortalCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField(allow_null=True)
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    shipping = PortalCustomerShippingSerializer(allow_null=True)
    tax_ids = TaxIdSerializer(many=True)


class PortalCustomerUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    legal_name = serializers.CharField(allow_null=True, required=False)
    legal_number = serializers.CharField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    phone = serializers.CharField(allow_null=True, required=False)
    address = AddressSerializer(required=False)
    shipping = PortalCustomerShippingUpdateSerializer(allow_null=True, required=False)
