from __future__ import annotations

from django.db import models
from djmoney.money import Money

from apps.accounts.models import Account

from .choices import ShippingRateStatus, ShippingRateTaxPolicy
from .querysets import ShippingRateQuerySet


class ShippingRateManager(models.Manager.from_queryset(ShippingRateQuerySet)):  # type: ignore[misc]
    def create_shipping_rate(
        self,
        account: Account,
        name: str,
        code: str | None,
        currency: str | None,
        amount: Money | None,
        tax_policy: ShippingRateTaxPolicy | None,
        metadata: dict | None = None,
    ):
        currency = currency or account.default_currency
        return self.create(
            account=account,
            name=name,
            code=code,
            currency=currency,
            amount=amount or Money(0, currency),
            tax_policy=tax_policy or ShippingRateTaxPolicy.MATCH_GOODS,
            status=ShippingRateStatus.ACTIVE,
            metadata=metadata or {},
        )
