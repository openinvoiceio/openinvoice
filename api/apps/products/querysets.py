from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account


class ProductQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def with_prices(self):
        return (
            self.prefetch_related("prices")
            .select_related("default_price")
            .annotate(prices_count=models.Count("prices"))
        )
