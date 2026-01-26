from __future__ import annotations

from typing import TYPE_CHECKING

import stripe
from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account

    from .models import StripeCustomer


class StripeCustomerManager(models.Manager):
    def ensure_for_account(self, account: Account) -> StripeCustomer:
        try:
            return self.get(account=account)
        except self.model.DoesNotExist:
            stripe_customer = stripe.Customer.create(
                email=account.email,
                name=account.name,
                metadata={"account_id": str(account.id)},
            )
            return self.create(customer_id=stripe_customer.id, account=account)


class StripeSubscriptionManager(models.Manager):
    pass
