from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import stripe
from django.apps import apps
from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models import Account

    from .models import StripeCustomer, StripeSubscription


class StripeCustomerManager(models.Manager["StripeCustomer"]):
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


class StripeSubscriptionManager(models.Manager["StripeSubscription"]):
    def record_created_event(self, event: stripe.Event) -> StripeSubscription:
        StripeCustomer = apps.get_model("stripe", "StripeCustomer")
        stripe_customer = StripeCustomer.objects.get(customer_id=event.data.object["customer"])
        price_id = event.data.object["items"]["data"][0]["price"]["id"]

        return self.create(
            stripe_customer=stripe_customer,
            subscription_id=event.data.object["id"],
            price_id=price_id,
            product_name="",
            status=event.data.object["status"],
            started_at=datetime.fromtimestamp(event.data.object["current_period_start"], tz=UTC),
        )

    def record_updated_event(self, event: stripe.Event) -> StripeSubscription:
        StripeCustomer = apps.get_model("stripe", "StripeCustomer")
        stripe_customer = StripeCustomer.objects.get(customer_id=event.data.object["customer"])
        price_id = event.data.object["items"]["data"][0]["price"]["id"]
        canceled_at = (
            datetime.fromtimestamp(event.data.object["canceled_at"], tz=UTC)
            if event.data.object["canceled_at"]
            else None
        )
        ended_at = (
            datetime.fromtimestamp(event.data.object["ended_at"], tz=UTC) if event.data.object["ended_at"] else None
        )

        stripe_subscription, _ = self.update_or_create(
            subscription_id=event.data.object["id"],
            defaults={
                "stripe_customer": stripe_customer,
                "price_id": price_id,
                "status": event.data.object["status"],
                "canceled_at": canceled_at,
                "ended_at": ended_at,
            },
        )

        return stripe_subscription
