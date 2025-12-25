from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models

from .querysets import TaxRateQuerySet

if TYPE_CHECKING:
    from apps.accounts.models import Account
    from apps.customers.models import Customer


class TaxRateManager(models.Manager.from_queryset(TaxRateQuerySet)):
    def create_tax_rate(
        self,
        account,
        name: str,
        description: str | None,
        percentage: Decimal,
        country: str | None,
    ):
        return self.create(
            account=account,
            name=name,
            description=description,
            percentage=percentage,
            country=country,
        )


class TaxIdManager(models.Manager["TaxId"]):
    def create_tax_id(
        self,
        *,
        type_: str,
        number: str,
        country: str | None,
    ):
        return self.create(
            type=type_,
            number=number,
            country=country,
        )

    def from_account(self, account: Account):
        return [
            self.create_tax_id(
                type_=tax_id.type,
                number=tax_id.number,
                country=tax_id.country,
            )
            for tax_id in account.tax_ids.all()
        ]

    def from_customer(self, customer: Customer):
        return [
            self.create_tax_id(
                type_=tax_id.type,
                number=tax_id.number,
                country=tax_id.country,
            )
            for tax_id in customer.tax_ids.all()
        ]
