from __future__ import annotations

import uuid

from django.db import models

from .choices import NumberingSystemAppliesTo


class NumberingSystemQuerySet(models.QuerySet["NumberingSystem"]):
    def for_account(self, account_id: uuid.UUID) -> NumberingSystemQuerySet:
        return self.filter(account_id=account_id)

    def for_applies_to(
        self,
        applies_to: NumberingSystemAppliesTo,
    ) -> NumberingSystemQuerySet:
        return self.filter(applies_to=applies_to)
