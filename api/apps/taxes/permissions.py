from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import TaxRate


class MaxTaxRatesLimit(EntitlementLimit):
    key = EntitlementCode.MAX_TAX_RATES
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return TaxRate.objects.filter(account_id=request.account.id).count()
