from __future__ import annotations

from datetime import timedelta

import stripe
from django.conf import settings
from django.db import models
from django.utils import timezone

from .managers import StripeCustomerManager, StripeSubscriptionManager
from .querysets import StripeSubscriptionQuerySet


class StripeCustomer(models.Model):
    account = models.OneToOneField(
        "accounts.Account", on_delete=models.CASCADE, related_name="stripe_customer", primary_key=True
    )
    customer_id = models.CharField(max_length=128, null=False)

    objects = StripeCustomerManager()

    def create_billing_portal_session(self) -> stripe.billing_portal.Session:
        configurations = stripe.billing_portal.Configuration.list()
        if configurations.data:
            configuration = configurations.data[0]
        else:
            configuration = stripe.billing_portal.Configuration.create(**settings.STRIPE_BILLING_PORTAL_CONFIGURATION)

        return stripe.billing_portal.Session.create(
            customer=self.customer_id,
            return_url=settings.BILLING_URL,
            configuration=configuration.id,
        )

    def create_checkout_session(self, price_id: str) -> stripe.checkout.Session:
        trial_end = timezone.now().replace(microsecond=0) + timedelta(days=settings.STRIPE_TRIAL_DAYS)

        return stripe.checkout.Session.create(
            customer=self.customer_id,
            payment_method_types=settings.STRIPE_PAYMENT_METHOD_TYPES,  # type: ignore[arg-type]
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=settings.BILLING_URL,
            cancel_url=settings.BILLING_URL,
            allow_promotion_codes=True,
            subscription_data={"trial_end": int(trial_end.timestamp())},
        )


class StripeSubscription(models.Model):
    subscription_id = models.CharField(max_length=100, primary_key=True)
    price_id = models.CharField(max_length=100)
    stripe_customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE, related_name="subscriptions")
    product_name = models.CharField(max_length=500)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)

    objects = StripeSubscriptionManager.from_queryset(StripeSubscriptionQuerySet)()

    class Meta:
        indexes = [
            models.Index(fields=["stripe_customer", "status"]),
        ]
