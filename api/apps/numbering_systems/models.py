from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta

from django.db import models
from django.utils import timezone

from .enums import NumberingSystemAppliesTo, NumberingSystemResetInterval
from .formatting import render_template
from .managers import NumberingSystemManager

# TODO: implement uniqueness maintenance
# TODO: implement starting point of numbering system


"""
- how to handle draft invoices and active invoices sequence?
"""


class NumberingSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True)
    applies_to = models.CharField(max_length=50, choices=NumberingSystemAppliesTo.choices)
    reset_interval = models.CharField(max_length=50, choices=NumberingSystemResetInterval.choices)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="numbering_systems")
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NumberingSystemManager()

    class Meta:
        ordering = ["-created_at"]

    def has_documents(self) -> bool:
        match self.applies_to:
            case NumberingSystemAppliesTo.INVOICE:
                return self.invoices.exists()
            case NumberingSystemAppliesTo.CREDIT_NOTE:
                return self.credit_notes.exists()
            case NumberingSystemAppliesTo.QUOTE:
                return self.quotes.exists()
            case _:
                return False

    def update(
        self,
        template: str,
        description: str | None,
        reset_interval: NumberingSystemResetInterval | None,
    ) -> None:
        self.description = description

        if not self.has_documents():
            self.template = template
            self.reset_interval = reset_interval or NumberingSystemResetInterval.NEVER

        self.save()

    def render_number(self, *, count: int, effective_at: datetime) -> str:
        return render_template(template=self.template, count=count, effective_at=effective_at)

    def calculate_bounds(self, effective_at: datetime) -> tuple[datetime | None, datetime | None]:
        now = timezone.localtime(effective_at)
        tz = now.tzinfo

        match self.reset_interval:
            case NumberingSystemResetInterval.NEVER:
                return None, None
            case NumberingSystemResetInterval.WEEKLY:
                delta_days = now.weekday() % 7
                start_date = now.date() - timedelta(days=delta_days)
                start = datetime.combine(start_date, time.min, tzinfo=tz)
                end = start + timedelta(days=7)
                return start, end
            case NumberingSystemResetInterval.MONTHLY:
                start = datetime(now.year, now.month, 1, tzinfo=tz)
                if now.month == 12:
                    end = datetime(now.year + 1, 1, 1, tzinfo=tz)
                else:
                    end = datetime(now.year, now.month + 1, 1, tzinfo=tz)
                return start, end
            case NumberingSystemResetInterval.QUARTERLY:
                quarter = (now.month - 1) // 3 + 1
                start_month = 3 * (quarter - 1) + 1
                start = datetime(now.year, start_month, 1, tzinfo=tz)
                if start_month == 10:
                    end = datetime(now.year + 1, 1, 1, tzinfo=tz)
                else:
                    end = datetime(now.year, start_month + 3, 1, tzinfo=tz)
                return start, end
            case NumberingSystemResetInterval.YEARLY:
                start = datetime(now.year, 1, 1, tzinfo=tz)
                end = datetime(now.year + 1, 1, 1, tzinfo=tz)
                return start, end
            case _:
                return None, None
