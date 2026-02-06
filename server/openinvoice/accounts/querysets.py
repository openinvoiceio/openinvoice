from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from openinvoice.users.models import User

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account

from .choices import InvitationStatus


class AccountQuerySet(models.QuerySet):
    def for_user(self, user: User):
        return self.filter(members=user)

    def active(self):
        return self.filter(is_active=True)

    def eager_load(self):
        return self.select_related("default_business_profile", "default_business_profile__address").prefetch_related(
            "default_business_profile__tax_ids",
            "tax_ids",
        )


class BusinessProfileQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(accounts=account)


class InvitationQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

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
