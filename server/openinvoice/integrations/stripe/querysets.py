from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account


class StripeConnectionQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)
