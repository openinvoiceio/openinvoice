import uuid

from django.db import models
from djmoney.models.fields import MoneyField

from .managers import CouponManager


class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency", null=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="coupons")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CouponManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="check_coupon_amount_and_percentage_mutually_exclusive",
                condition=models.Q(amount__isnull=False, percentage__isnull=True)
                | models.Q(amount__isnull=True, percentage__isnull=False),
            )
        ]

    def update(self, name: str | None = None) -> None:
        self.name = name
        self.save(update_fields=["name", "updated_at"])

    def deactivate(self) -> None:
        if not self.is_active:
            return

        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])
