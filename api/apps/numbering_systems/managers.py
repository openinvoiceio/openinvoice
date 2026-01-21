from __future__ import annotations

import typing
import uuid

from django.conf import settings
from django.db import models

from .choices import NumberingSystemAppliesTo, NumberingSystemResetInterval
from .querysets import NumberingSystemQuerySet

if typing.TYPE_CHECKING:
    from .models import NumberingSystem


class NumberingSystemManager(models.Manager.from_queryset(NumberingSystemQuerySet)):  # type: ignore[misc]
    def create_numbering_system(
        self,
        *,
        account_id: uuid.UUID,
        template: str,
        description: str | None,
        applies_to: NumberingSystemAppliesTo,
        reset_interval: NumberingSystemResetInterval | None,
    ) -> NumberingSystem:
        return self.create(
            account_id=account_id,
            template=template,
            description=description,
            applies_to=applies_to,
            reset_interval=reset_interval or NumberingSystemResetInterval.NEVER,
        )

    def create_default_invoice_numbering_system(self, *, account_id: uuid.UUID) -> NumberingSystem:
        return self.create_numbering_system(
            account_id=account_id,
            template=settings.ACCOUNT_INVOICE_NUMBERING_SYSTEM_TEMPLATE,
            description=settings.ACCOUNT_INVOICE_NUMBERING_SYSTEM_DESCRIPTION,
            applies_to=NumberingSystemAppliesTo.INVOICE,
            reset_interval=NumberingSystemResetInterval.NEVER,
        )

    def create_default_credit_note_numbering_system(self, *, account_id: uuid.UUID) -> NumberingSystem:
        return self.create_numbering_system(
            account_id=account_id,
            template=settings.ACCOUNT_CREDIT_NOTE_NUMBERING_SYSTEM_TEMPLATE,
            description=settings.ACCOUNT_CREDIT_NOTE_NUMBERING_SYSTEM_DESCRIPTION,
            applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
            reset_interval=NumberingSystemResetInterval.NEVER,
        )
