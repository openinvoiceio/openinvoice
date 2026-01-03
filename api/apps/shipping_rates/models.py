import uuid

from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from .enums import ShippingRateTaxPolicy
from .managers import ShippingRateManager


class ShippingRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    tax_policy = models.CharField(max_length=16, choices=ShippingRateTaxPolicy.choices)
    is_active = models.BooleanField()
    metadata = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="shipping_rates")

    objects = ShippingRateManager()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        name: str,
        code: str | None,
        currency: str,
        amount: Money,
        tax_policy: ShippingRateTaxPolicy,
        metadata: dict,
    ) -> None:
        self.name = name
        self.code = code
        self.currency = currency
        self.amount = amount
        self.tax_policy = tax_policy
        self.metadata = metadata
        self.save()

    def archive(self) -> None:
        if not self.is_active:
            return

        self.is_active = False
        self.archived_at = timezone.now()
        self.save(update_fields=["is_active", "archived_at", "updated_at"])

    def unarchive(self) -> None:
        if self.is_active:
            return

        self.is_active = True
        self.archived_at = None
        self.save(update_fields=["is_active", "archived_at", "updated_at"])
