import django_filters

from common.filters import CharInFilter

from .models import Coupon


class CouponFilterSet(django_filters.FilterSet):
    currency = CharInFilter(field_name="currency")

    class Meta:
        model = Coupon
        fields = []
