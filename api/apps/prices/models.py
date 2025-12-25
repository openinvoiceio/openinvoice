import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from common.calculations import zero

from .enums import PriceModel
from .managers import PriceManager


class Price(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    model = models.CharField(max_length=16, choices=PriceModel.choices, default=PriceModel.FLAT)
    is_active = models.BooleanField()
    is_used = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="prices")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        null=False,
        related_name="prices",
    )

    objects = PriceManager()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        amount: Money,
        currency: str,
        metadata: dict,
        code: str | None,
    ) -> None:
        self.amount = amount
        self.currency = currency
        self.code = code
        self.metadata = metadata
        self.save(update_fields=["amount", "currency", "code", "updated_at"])

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

    def mark_as_used(self) -> None:
        if self.is_used:
            return

        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])

    def add_tier(self, unit_amount: Money, from_value: int, to_value: int | None) -> "PriceTier":
        return self.tiers.create(
            unit_amount=unit_amount,
            currency=self.currency,
            from_value=from_value,
            to_value=to_value,
        )

    def calculate_amount(self, quantity: int) -> Money:  # noqa: C901
        if quantity <= 0:
            return Money(0, self.currency)

        match self.model:
            case PriceModel.FLAT:
                return self.amount * quantity

            case PriceModel.VOLUME:
                for tier in self.tiers.all():
                    if quantity < tier.from_value:
                        continue
                    if tier.to_value is None or quantity <= tier.to_value:
                        return tier.unit_amount * quantity
                return zero(self.currency)

            case PriceModel.GRADUATED:
                amount = zero(self.currency)
                remaining_quantity = quantity

                for tier in self.tiers.all():
                    if remaining_quantity <= 0:
                        break
                    if quantity < tier.from_value:
                        break

                    if tier.to_value is None:
                        units = remaining_quantity
                    else:
                        units = min(tier.to_value - tier.from_value + 1, remaining_quantity)

                    amount += tier.unit_amount * units
                    remaining_quantity -= units

                return amount

            case _:
                return zero(self.currency)

    def calculate_unit_amount(self, quantity: int) -> Money:
        if quantity <= 0:
            return Money(0, self.currency)

        total = self.calculate_amount(quantity)
        return total / quantity


class PriceTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.ForeignKey("prices.Price", on_delete=models.CASCADE, related_name="tiers")
    currency = models.CharField(max_length=3)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    from_value = models.PositiveIntegerField()
    to_value = models.PositiveIntegerField(null=True, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["from_value"]
        constraints = [
            models.UniqueConstraint(fields=["price", "from_value"], name="unique_price_tier_from"),
            models.CheckConstraint(
                name="price_tier_upper_bound",
                condition=Q(to_value__isnull=True) | Q(to_value__gte=models.F("from_value")),
            ),
        ]
