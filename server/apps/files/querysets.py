from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Q

if TYPE_CHECKING:
    from apps.accounts.models import Account
    from apps.users.models import User


class FileQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def for_user(self, user: User):
        return self.filter(uploader=user)

    def visible_to(self, account: Account, user: User):
        return self.filter(Q(account=account) | Q(uploader=user))
