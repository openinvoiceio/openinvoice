from __future__ import annotations

from decimal import Decimal

from django.db import models

from .choices import CouponStatus


class CouponManager(models.Manager):
    def create_coupon(
        self,
        account,
        name: str,
        currency: str | None,
        amount: Decimal | None,
        percentage: Decimal | None,
    ):
        return self.create(
            account=account,
            name=name,
            currency=currency or account.default_currency,
            amount=amount,
            percentage=percentage,
            status=CouponStatus.ACTIVE,
        )
