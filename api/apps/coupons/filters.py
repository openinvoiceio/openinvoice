import django_filters

from common.filters import CharInFilter

from .models import Coupon


class CouponFilter(django_filters.FilterSet):
    currency = CharInFilter(field_name="currency", lookup_expr="in")

    class Meta:
        model = Coupon
        fields = []
