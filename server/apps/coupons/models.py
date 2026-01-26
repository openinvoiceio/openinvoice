import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone
from djmoney import settings as djmoney_settings
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from common.calculations import zero

from .choices import CouponStatus
from .managers import CouponManager
from .querysets import CouponQuerySet


class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency", null=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="coupons")
    status = models.CharField(max_length=20, choices=CouponStatus.choices, default=CouponStatus.ACTIVE)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CouponManager.from_queryset(CouponQuerySet)()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="check_coupon_amount_and_percentage_mutually_exclusive",
                condition=models.Q(amount__isnull=False, percentage__isnull=True)
                | models.Q(amount__isnull=True, percentage__isnull=False),
            )
        ]

    def update(self, name: str) -> None:
        self.name = name
        self.save()

    def archive(self) -> None:
        if self.status == CouponStatus.ARCHIVED:
            return

        self.status = CouponStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()

    def restore(self) -> None:
        if self.status == CouponStatus.ACTIVE:
            return

        self.status = CouponStatus.ACTIVE
        self.archived_at = None
        self.save()

    def calculate_amount(self, base_amount: Money) -> Money:
        if self.amount is not None:
            if self.amount <= zero(self.currency):
                return zero(self.currency)
            return min(self.amount, base_amount)

        if self.percentage is not None:
            percentage_amount = base_amount * (self.percentage / Decimal(100))
            if percentage_amount <= zero(self.currency):
                return zero(self.currency)
            return min(percentage_amount, base_amount)

        return zero(self.currency)
