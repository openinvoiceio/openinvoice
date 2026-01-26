from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .choices import PaymentStatus

if TYPE_CHECKING:
    from apps.accounts.models import Account


class PaymentQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def succeeded(self):
        return self.filter(status=PaymentStatus.SUCCEEDED)
