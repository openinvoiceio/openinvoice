from __future__ import annotations

from django.db import models
from djmoney.money import Money

from apps.products.models import Product

from .choices import PriceModel, PriceStatus


class PriceManager(models.Manager):
    def create_price(
        self,
        amount: Money | None,
        product: Product,
        currency: str,
        metadata: dict | None = None,
        code: str | None = None,
        model: str | None = None,
    ):
        return self.create(
            account=product.account,
            product=product,
            currency=currency,
            amount=amount or Money(0, currency),
            model=model or PriceModel.FLAT,
            status=PriceStatus.ACTIVE,
            metadata=metadata or {},
            code=code,
        )
