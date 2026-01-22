from __future__ import annotations

from django.db import models

from .choices import CouponStatus


class CouponQuerySet(models.QuerySet):
    def for_account(self, account_id: str):
        return self.filter(account_id=account_id)

    def active(self):
        return self.filter(status=CouponStatus.ACTIVE)
