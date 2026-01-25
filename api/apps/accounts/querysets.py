from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.users.models import User

if TYPE_CHECKING:
    from apps.accounts.models import Account

from .choices import InvitationStatus


class AccountQuerySet(models.QuerySet):
    def for_user(self, user: User):
        return self.filter(members=user)

    def active(self):
        return self.filter(is_active=True)

    def eager_load(self):
        return self.select_related("address").prefetch_related("tax_ids")


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
