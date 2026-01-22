from __future__ import annotations

from django.db import models

from apps.users.models import User

from .choices import InvitationStatus


class AccountQuerySet(models.QuerySet):
    def for_user(self, user: User):
        return self.filter(members=user)

    def active(self):
        return self.filter(is_active=True)


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
