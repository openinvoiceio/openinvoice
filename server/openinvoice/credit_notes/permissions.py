from django.utils import timezone

from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import CreditNote


class MaxCreditNotesLimit(WithinLimit):
    key = LimitCode.MAX_CREDIT_NOTES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return CreditNote.objects.for_account(request.account).filter(created_at__month=now.month).count()
