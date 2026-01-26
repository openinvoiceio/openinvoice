from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account


class ShippingRateQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)
