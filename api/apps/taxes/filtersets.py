import django_filters

from .models import TaxRate


class TaxRateFilterSet(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(field_name="is_active", lookup_expr="exact")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = TaxRate
        fields = []
