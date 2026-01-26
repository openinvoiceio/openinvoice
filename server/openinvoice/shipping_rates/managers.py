from django.db import models
from djmoney.money import Money

from openinvoice.accounts.models import Account

from .choices import ShippingRateStatus


class ShippingRateManager(models.Manager):
    def create_shipping_rate(
        self,
        account: Account,
        name: str,
        code: str | None,
        currency: str | None,
        amount: Money | None,
        metadata: dict | None = None,
    ):
        currency = currency or account.default_currency
        return self.create(
            account=account,
            name=name,
            code=code,
            currency=currency,
            amount=amount or Money(0, currency),
            status=ShippingRateStatus.ACTIVE,
            metadata=metadata or {},
        )
