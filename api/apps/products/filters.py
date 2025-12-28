import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    price_currency = django_filters.CharFilter(method="filter_price_currency")
    has_active_prices = django_filters.BooleanFilter(field_name="prices", method="filter_has_active_prices")
    is_active = django_filters.BooleanFilter(field_name="is_active", lookup_expr="exact")
    created_at_eq = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="exact")
    created_at_gt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gt")
    created_at_gte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lt = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt")
    created_at_lte = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Product
        fields: list[str] = []

    def filter_price_currency(self, queryset, _, value):
        return queryset.filter(prices__currency=value).distinct()

    def filter_has_active_prices(self, queryset, _, value):
        if value:
            return queryset.filter(prices__is_active=True).distinct()
        return queryset.exclude(prices__is_active=True).distinct()
