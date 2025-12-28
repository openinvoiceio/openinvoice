from common.enums import LimitCode
from common.permissions import WithinLimit

from .models import Coupon


class MaxCouponsLimit(WithinLimit):
    key = LimitCode.MAX_COUPONS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Coupon.objects.filter(account_id=request.account.id).count()
