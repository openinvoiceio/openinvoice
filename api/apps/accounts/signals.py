from typing import Any

import structlog
from django.dispatch import receiver
from django_structlog import signals


@receiver(signals.bind_extra_request_metadata)
def bind_account_id(request, **_: Any) -> None:
    account = getattr(request, "account", None)
    account_id = getattr(account, "id", None)
    structlog.contextvars.bind_contextvars(account_id=str(account_id))
