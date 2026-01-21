from common.choices import LimitCode
from common.permissions import WithinLimit

from .models import ShippingRate


class MaxShippingRatesLimit(WithinLimit):
    key = LimitCode.MAX_SHIPPING_RATES
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return ShippingRate.objects.filter(account_id=request.account.id).count()
