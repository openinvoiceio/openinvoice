from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import Customer


class MaxCustomersLimit(EntitlementLimit):
    key = EntitlementCode.MAX_CUSTOMERS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Customer.objects.filter(account_id=request.account.id).count()
