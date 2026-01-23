from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account

from .choices import NumberingSystemAppliesTo


class NumberingSystemQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def for_applies_to(self, applies_to: NumberingSystemAppliesTo):
        return self.filter(applies_to=applies_to)
