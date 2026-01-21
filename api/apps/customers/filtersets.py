import django_filters

from common.filters import CharInFilter

from .models import Customer


class CustomerFilterSet(django_filters.FilterSet):
    currency = CharInFilter(field_name="currency")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Customer
        fields = []
