from rest_framework import serializers

from openinvoice.customers.serializers import CustomerSerializer
from openinvoice.invoices.serializers import InvoiceSerializer
from openinvoice.products.serializers import ProductSerializer


class SearchSerializer(serializers.Serializer):
    invoices = InvoiceSerializer(many=True)
    products = ProductSerializer(many=True)
    customers = CustomerSerializer(many=True)
