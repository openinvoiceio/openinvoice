from django.utils import timezone

from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import Invoice


class MaxInvoicesLimit(EntitlementLimit):
    key = EntitlementCode.MAX_INVOICES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Invoice.objects.filter(account_id=request.account.id, created_at__month=now.month).count()
