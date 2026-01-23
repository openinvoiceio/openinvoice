from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db import models

from .managers import CustomerManager

if TYPE_CHECKING:
    from apps.files.models import File
    from apps.numbering_systems.models import NumberingSystem


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True)
    net_payment_term = models.IntegerField(null=True)
    invoice_numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.CASCADE,
        related_name="invoice_numbering_customers",
        null=True,
    )
    credit_note_numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.CASCADE,
        related_name="credit_note_numbering_customers",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    metadata = models.JSONField(default=dict)
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="customers",
    )
    billing_address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.CASCADE,
        related_name="customer_billing_address",
        null=False,
    )
    shipping_address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.CASCADE,
        related_name="customer_shipping_address",
        null=False,
    )
    logo = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="customer_logo")
    tax_rates = models.ManyToManyField(
        "tax_rates.TaxRate",
        through="CustomerTaxRate",
        related_name="customers",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="customers")

    objects = CustomerManager()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        name: str,
        legal_name: str | None,
        legal_number: str | None,
        email: str | None,
        phone: str | None,
        description: str | None,
        currency: str | None,
        net_payment_term: int | None,
        invoice_numbering_system: NumberingSystem | None,
        credit_note_numbering_system: NumberingSystem | None,
        metadata: dict,
        logo: File | None,
    ) -> None:
        self.name = name
        self.legal_name = legal_name
        self.legal_number = legal_number
        self.email = email
        self.phone = phone
        self.description = description
        self.currency = currency
        self.net_payment_term = net_payment_term
        self.invoice_numbering_system = invoice_numbering_system
        self.credit_note_numbering_system = credit_note_numbering_system
        self.metadata = metadata
        self.logo = logo

        self.save()

    def update_portal_profile(
        self,
        name: str,
        email: str | None,
        phone: str | None,
        legal_name: str | None,
        legal_number: str | None,
    ) -> None:
        self.name = name
        self.legal_name = legal_name
        self.legal_number = legal_number
        self.email = email
        self.phone = phone

        self.save(update_fields=["name", "legal_name", "legal_number", "email", "phone"])


class CustomerTaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="customer_tax_rates",
    )
    tax_rate = models.ForeignKey(
        "tax_rates.TaxRate",
        on_delete=models.CASCADE,
        related_name="customer_tax_rates",
    )

    class Meta:
        unique_together = ("customer", "tax_rate")
