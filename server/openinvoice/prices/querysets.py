from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account


class PriceQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def eager_load(self):
        return self.select_related("product").prefetch_related("tiers")
