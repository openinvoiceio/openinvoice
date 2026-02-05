from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account


class CustomerQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def eager_load(self):
        return self.select_related(
            "default_billing_profile",
            "default_billing_profile__address",
            "default_shipping_profile",
            "default_shipping_profile__address",
            "logo",
        ).prefetch_related(
            "default_billing_profile__tax_rates",
            "default_billing_profile__tax_ids",
        )


class BillingProfileQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(customers__account=account).distinct()


class ShippingProfileQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(customers__account=account).distinct()
