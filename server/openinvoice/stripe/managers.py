from __future__ import annotations

from typing import TYPE_CHECKING

import stripe
from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account

    from .models import StripeCustomer


class StripeCustomerManager(models.Manager):
    def ensure_for_account(self, account: Account) -> StripeCustomer:
        try:
            return self.get(account=account)
        except self.model.DoesNotExist:
            stripe_customer = stripe.Customer.create(
                email=account.default_business_profile.email,
                name=account.default_business_profile.name,
                metadata={"account_id": str(account.id)},
            )
            return self.create(customer_id=stripe_customer.id, account=account)


class StripeSubscriptionManager(models.Manager):
    pass
