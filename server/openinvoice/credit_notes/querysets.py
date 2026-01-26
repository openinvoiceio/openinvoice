from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Sum
from djmoney.money import Money

from .choices import CreditNoteStatus

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account


class CreditNoteQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def issued(self):
        return self.filter(status=CreditNoteStatus.ISSUED)

    def total_amount(self, *, currency: str) -> Money:
        total = self.aggregate(total=Sum("total_amount")).get("total")
        if isinstance(total, Money):
            return total

        return Money(total or Decimal("0"), currency)


class CreditNoteTaxQuerySet(models.QuerySet):
    def for_credit_note(self):
        return self.filter(credit_note_line__isnull=True)

    def for_lines(self):
        return self.filter(credit_note_line__isnull=False)

    def has_lines(self):
        return self.for_lines().exists()

    def breakdown(self):
        return (
            self.values("name", "currency", "rate")
            .annotate(amount=models.Sum("amount"))
            .order_by("name", "currency", "rate")
        )
