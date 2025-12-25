import django_filters

from .models import TaxRate


class TaxRateFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(field_name="is_active", lookup_expr="exact")
    created_at_eq = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="exact")
    created_at_gt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gt")
    created_at_gte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt")
    created_at_lte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = TaxRate
        fields: list[str] = []
