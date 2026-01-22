import django_filters

from common.filters import CharInFilter

from .choices import CouponStatus
from .models import Coupon


class CouponFilterSet(django_filters.FilterSet):
    currency = CharInFilter(field_name="currency")
    status = django_filters.ChoiceFilter(field_name="status", choices=CouponStatus.choices)

    class Meta:
        model = Coupon
        fields = []
