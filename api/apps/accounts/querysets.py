from __future__ import annotations

from django.db import models
from django.db.models import Prefetch

from apps.stripe.constants import STRIPE_ACTIVE_SUBSCRIPTION_STATUSES
from apps.stripe.models import StripeSubscription
from apps.users.models import User

from .enums import InvitationStatus


class AccountQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def for_user(self, user: User):
        return self.filter(members=user)

    def with_subscriptions(self):
        return self.select_related("stripe_customer").prefetch_related(
            Prefetch(
                "stripe_customer__subscriptions",
                queryset=StripeSubscription.objects.filter(status__in=STRIPE_ACTIVE_SUBSCRIPTION_STATUSES),
                to_attr="active_subscriptions",
            ),
        )


class InvitationQuerySet(models.QuerySet):
    def pending_for(self, code: str, user: User):
        return (
            self.select_related("account")
            .filter(
                code=code,
                email=user.email,
                status=InvitationStatus.PENDING,
                account__is_active=True,
            )
            .first()
        )
