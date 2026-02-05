from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import TaxRate


class MaxTaxRatesLimit(WithinLimit):
    key = LimitCode.MAX_TAX_RATES
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return TaxRate.objects.for_account(request.account).count()
