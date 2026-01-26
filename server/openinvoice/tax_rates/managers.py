from decimal import Decimal

from django.db import models


class TaxRateManager(models.Manager):
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
