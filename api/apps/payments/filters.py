import django_filters

from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    invoice_id = django_filters.UUIDFilter(field_name="invoices__id")

    class Meta:
        model = Payment
        fields: list[str] = []
