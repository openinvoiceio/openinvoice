from rest_framework import serializers

from apps.customers.serializers import CustomerSerializer
from apps.invoices.serializers import InvoiceSerializer
from apps.products.serializers import ProductSerializer


class SearchSerializer(serializers.Serializer):
    invoices = InvoiceSerializer(many=True)
    products = ProductSerializer(many=True)
    customers = CustomerSerializer(many=True)
