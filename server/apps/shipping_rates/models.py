import uuid

from django.db import models
from django.utils import timezone
from djmoney import settings as djmoney_settings
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from .choices import ShippingRateStatus
from .managers import ShippingRateManager
from .querysets import ShippingRateQuerySet


class ShippingRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    status = models.CharField(
        max_length=20,
        choices=ShippingRateStatus.choices,
        default=ShippingRateStatus.ACTIVE,
    )
    metadata = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="shipping_rates")

    objects = ShippingRateManager.from_queryset(ShippingRateQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        name: str,
        code: str | None,
        currency: str,
        amount: Money,
        metadata: dict,
    ) -> None:
        self.name = name
        self.code = code
        self.currency = currency
        self.amount = amount
        self.metadata = metadata
        self.save()

    def archive(self) -> None:
        if self.status == ShippingRateStatus.ARCHIVED:
            return

        self.status = ShippingRateStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()

    def restore(self) -> None:
        if self.status == ShippingRateStatus.ACTIVE:
            return

        self.status = ShippingRateStatus.ACTIVE
        self.archived_at = None
        self.save()
