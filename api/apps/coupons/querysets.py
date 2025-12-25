from __future__ import annotations

from django.db import models


class CouponQuerySet(models.QuerySet["Coupon"]):
    def for_account(self, account_id: str):
        return self.filter(account_id=account_id)

    def active(self):
        return self.filter(is_active=True)
