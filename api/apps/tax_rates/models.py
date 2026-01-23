import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone
from djmoney.money import Money

from common.calculations import zero

from .choices import TaxRateStatus
from .managers import TaxRateManager
from .querysets import TaxRateQuerySet


class TaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    country = models.CharField(max_length=2, null=True)
    status = models.CharField(max_length=20, choices=TaxRateStatus.choices, default=TaxRateStatus.ACTIVE)
    archived_at = models.DateTimeField(null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="tax_rates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaxRateManager.from_queryset(TaxRateQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        name: str,
        description: str | None,
        country: str | None,
    ) -> None:
        self.name = name
        self.description = description
        self.country = country

        self.save()

    def archive(self) -> None:
        if self.status == TaxRateStatus.ARCHIVED:
            return

        self.status = TaxRateStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()

    def restore(self) -> None:
        if self.status == TaxRateStatus.ACTIVE:
            return

        self.status = TaxRateStatus.ACTIVE
        self.archived_at = None
        self.save()

    def calculate_amount(self, base_amount: Money) -> Money:
        if self.percentage <= 0:
            return zero(base_amount.currency)

        return base_amount * (self.percentage / Decimal(100))
