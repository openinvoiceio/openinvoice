from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import Coupon


class MaxCouponsLimit(WithinLimit):
    key = LimitCode.MAX_COUPONS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Coupon.objects.for_account(request.account).count()
