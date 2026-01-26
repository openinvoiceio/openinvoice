import django_filters

from .choices import PriceStatus
from .models import Price


class PriceFilterSet(django_filters.FilterSet):
    currency = django_filters.CharFilter(field_name="currency", lookup_expr="exact")
    status = django_filters.ChoiceFilter(field_name="status", choices=PriceStatus.choices)
    product_id = django_filters.UUIDFilter(field_name="product_id", lookup_expr="exact")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Price
        fields = []
