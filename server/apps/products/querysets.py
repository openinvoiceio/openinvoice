from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account


class ProductQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def eager_load(self):
        return self.select_related("default_price").prefetch_related("default_price__tiers")

    def annotate_prices(self):
        return self.annotate(prices_count=models.Count("prices"))
