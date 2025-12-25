import django_filters

from common.filters import CharInFilter

from .models import Customer


class CustomerFilter(django_filters.FilterSet):
    currency_in = CharInFilter(field_name="currency", lookup_expr="in")
    created_at_eq = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="exact")
    created_at_gt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gt")
    created_at_gte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt")
    created_at_lte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Customer
        fields = ["currency", "created_at"]
