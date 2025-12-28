from common.enums import LimitCode
from common.permissions import WithinLimit

from .models import Customer


class MaxCustomersLimit(WithinLimit):
    key = LimitCode.MAX_CUSTOMERS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Customer.objects.filter(account_id=request.account.id).count()
