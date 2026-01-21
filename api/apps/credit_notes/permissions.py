from django.utils import timezone

from common.choices import LimitCode
from common.permissions import WithinLimit

from .models import CreditNote


class MaxCreditNotesLimit(WithinLimit):
    key = LimitCode.MAX_CREDIT_NOTES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return CreditNote.objects.filter(account_id=request.account.id, created_at__month=now.month).count()
