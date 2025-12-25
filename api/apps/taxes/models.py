import uuid

from django.db import models

from .enums import TaxIdType
from .managers import TaxIdManager, TaxRateManager


class TaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    country = models.CharField(max_length=2, null=True)
    is_active = models.BooleanField(default=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="tax_rates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaxRateManager()

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

        self.save(update_fields=["name", "description", "country", "updated_at"])

    def archive(self) -> None:
        if not self.is_active:
            return

        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def unarchive(self) -> None:
        if self.is_active:
            return

        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])


class TaxId(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=TaxIdType.choices)
    number = models.CharField(max_length=255)
    country = models.CharField(max_length=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaxIdManager()
