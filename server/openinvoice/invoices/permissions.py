from django.utils import timezone

from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import Invoice


class MaxInvoicesLimit(WithinLimit):
    key = LimitCode.MAX_INVOICES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Invoice.objects.for_account(request.account).filter(created_at__month=now.month).count()
