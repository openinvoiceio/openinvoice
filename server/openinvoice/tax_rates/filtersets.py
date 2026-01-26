import django_filters

from .choices import TaxRateStatus
from .models import TaxRate


class TaxRateFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(field_name="status", choices=TaxRateStatus.choices)
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = TaxRate
        fields = []
