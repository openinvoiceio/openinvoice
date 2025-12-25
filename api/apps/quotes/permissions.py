from django.utils import timezone

from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import Quote


class MaxQuotesLimit(EntitlementLimit):
    key = EntitlementCode.MAX_QUOTES_PER_MONTH
    methods = ["POST"]

    def get_usage(self, request) -> int:
        now = timezone.now()
        return Quote.objects.filter(account_id=request.account.id, created_at__month=now.month).count()
