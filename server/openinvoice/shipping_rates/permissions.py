from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import ShippingRate


class MaxShippingRatesLimit(WithinLimit):
    key = LimitCode.MAX_SHIPPING_RATES
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return ShippingRate.objects.for_account(request.account).count()
