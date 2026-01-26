from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account
    from openinvoice.customers.models import Customer


class TaxIdManager(models.Manager):
    def create_tax_id(
        self,
        type_: str,
        number: str,
        country: str | None,
    ):
        return self.create(
            type=type_,
            number=number,
            country=country,
        )

    def from_account(self, account: "Account"):
        return [
            self.create_tax_id(
                type_=tax_id.type,
                number=tax_id.number,
                country=tax_id.country,
            )
            for tax_id in account.tax_ids.all()
        ]

    def from_customer(self, customer: "Customer"):
        return [
            self.create_tax_id(
                type_=tax_id.type,
                number=tax_id.number,
                country=tax_id.country,
            )
            for tax_id in customer.tax_ids.all()
        ]
