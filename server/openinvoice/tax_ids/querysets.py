from __future__ import annotations

from django.db import models


class TaxIdQuerySet(models.QuerySet):
    def for_account(self, account):
        return self.filter(accounts=account)

    def for_customer(self, customer):
        return self.filter(customers=customer).distinct()

    def clone(self):
        return self.model.objects.bulk_create(
            [
                self.model(
                    type=tax_id.type,
                    number=tax_id.number,
                    country=tax_id.country,
                )
                for tax_id in self
            ]
        )
