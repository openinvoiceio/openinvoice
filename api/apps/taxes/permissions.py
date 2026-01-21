from common.choices import LimitCode
from common.permissions import WithinLimit

from .models import TaxRate


class MaxTaxRatesLimit(WithinLimit):
    key = LimitCode.MAX_TAX_RATES
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return TaxRate.objects.filter(account_id=request.account.id).count()
