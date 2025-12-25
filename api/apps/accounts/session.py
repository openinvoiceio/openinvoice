from rest_framework.request import Request

from .models import Account

ACTIVE_ACCOUNT_SESSION_KEY = "active_account_id"


def set_active_account_session(request: Request, account: Account) -> None:
    request.session[ACTIVE_ACCOUNT_SESSION_KEY] = str(account.id)


def remove_active_account_session(request: Request) -> None:
    request.session.pop(ACTIVE_ACCOUNT_SESSION_KEY, None)


def get_active_account_session(request: Request) -> str | None:
    return request.session.get(ACTIVE_ACCOUNT_SESSION_KEY, None)
