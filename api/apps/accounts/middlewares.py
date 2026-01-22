import structlog
from django.utils.deprecation import MiddlewareMixin

from .models import Account
from .session import get_active_account_session

logger = structlog.get_logger(__name__)


class AccountMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.account = None
        request.accounts = Account.objects.none()

        if not request.user.is_authenticated:
            return

        request.accounts = Account.objects.for_user(request.user).active()
        account_id = get_active_account_session(request)

        if account_id is None:
            request.account = request.accounts.first()
            return

        try:
            request.account = request.accounts.get(id=account_id)
        except Account.DoesNotExist:
            logger.warning("Active account not found", user_id=request.user.id, account_id=account_id)
