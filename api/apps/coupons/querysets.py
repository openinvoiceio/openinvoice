from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .choices import CouponStatus

if TYPE_CHECKING:
    from apps.accounts.models import Account


class CouponQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def active(self):
        return self.filter(status=CouponStatus.ACTIVE)
