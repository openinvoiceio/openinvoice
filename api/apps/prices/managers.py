from __future__ import annotations

from django.db import models
from djmoney.money import Money

from apps.products.models import Product

from .enums import PriceModel
from .querysets import PriceQuerySet


class PriceManager(models.Manager.from_queryset(PriceQuerySet)):  # type: ignore[misc]
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
            is_active=True,
            metadata=metadata or {},
            code=code,
        )
