from django.utils import timezone

from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .models import Quote


class MaxQuotesLimit(WithinLimit):
    key = LimitCode.MAX_QUOTES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Quote.objects.for_account(request.account).filter(created_at__month=now.month).count()
