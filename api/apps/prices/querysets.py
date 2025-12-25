from __future__ import annotations

from django.db import models


class PriceQuerySet(models.QuerySet):
    def for_account(self, account_id):
        return self.filter(account_id=account_id)
