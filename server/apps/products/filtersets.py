import django_filters

from apps.prices.choices import PriceStatus

from .choices import ProductStatus
from .models import Product


class ProductFilterSet(django_filters.FilterSet):
    price_currency = django_filters.CharFilter(method="filter_price_currency")
    has_active_prices = django_filters.BooleanFilter(field_name="prices", method="filter_has_active_prices")
    status = django_filters.ChoiceFilter(field_name="status", choices=ProductStatus.choices)
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Product
        fields = []

    def filter_price_currency(self, queryset, _, value):
        return queryset.filter(prices__currency=value).distinct()

    def filter_has_active_prices(self, queryset, _, value):
        if value:
            return queryset.filter(prices__status=PriceStatus.ACTIVE).distinct()
        return queryset.exclude(prices__status=PriceStatus.ACTIVE).distinct()
