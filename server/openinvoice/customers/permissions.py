from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import Customer


class MaxCustomersLimit(WithinLimit):
    key = LimitCode.MAX_CUSTOMERS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Customer.objects.for_account(request.account).count()
