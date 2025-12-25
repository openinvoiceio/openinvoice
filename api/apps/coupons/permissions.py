from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import Coupon


class MaxCouponsLimit(EntitlementLimit):
    key = EntitlementCode.MAX_COUPONS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Coupon.objects.filter(account_id=request.account.id).count()
