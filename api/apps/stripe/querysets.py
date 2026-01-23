from django.db import models

from apps.accounts.models import Account


class StripeSubscriptionQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(stripe_customer__account=account)

    def active(self):
        return self.filter(status__in=["active", "trialing"])
