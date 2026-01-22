import django_filters

from .choices import ShippingRateStatus
from .models import ShippingRate


class ShippingRateFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(field_name="status", choices=ShippingRateStatus.choices)

    class Meta:
        model = ShippingRate
        fields = []
