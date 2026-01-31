from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers

from common.fields import CurrencyField
from openinvoice.addresses.serializers import AddressSerializer
from openinvoice.customers.fields import CustomerRelatedField
from openinvoice.invoices.choices import InvoiceDocumentAudience, InvoiceStatus
from openinvoice.tax_ids.serializers import TaxIdSerializer


class PortalInvoiceDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    language = serializers.CharField()
    url = serializers.URLField(source="file.data.url", allow_null=True)


class PortalInvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    number = serializers.CharField(allow_null=True)
    status = serializers.ChoiceField(choices=InvoiceStatus.choices)
    currency = CurrencyField()
    issue_date = serializers.DateField(allow_null=True)
    due_date = serializers.DateField()
    total_amount = MoneyField(max_digits=19, decimal_places=2)
    documents = serializers.SerializerMethodField()

    def get_documents(self, invoice):
        documents = (
            invoice.documents.filter(audience__contains=[InvoiceDocumentAudience.CUSTOMER])
            .select_related("file")
            .order_by("created_at")
        )
        return PortalInvoiceDocumentSerializer(documents, many=True).data


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
