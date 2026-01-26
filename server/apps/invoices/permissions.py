from django.utils import timezone

from common.choices import LimitCode
from common.permissions import WithinLimit

from .models import Invoice


class MaxInvoicesLimit(WithinLimit):
    key = LimitCode.MAX_INVOICES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Invoice.objects.for_account(request.account).filter(created_at__month=now.month).count()
