from django.utils import timezone

from common.enums import LimitCode
from common.permissions import WithinLimit

from .models import Quote


class MaxQuotesLimit(WithinLimit):
    key = LimitCode.MAX_QUOTES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Quote.objects.filter(account_id=request.account.id, created_at__month=now.month).count()
