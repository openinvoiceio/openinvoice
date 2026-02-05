from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from djmoney import settings as djmoney_settings

from openinvoice.addresses.models import Address

from .managers import BillingProfileManager, CustomerManager, ShippingProfileManager
from .querysets import BillingProfileQuerySet, CustomerQuerySet, ShippingProfileQuerySet

if TYPE_CHECKING:
    from openinvoice.files.models import File
    from openinvoice.numbering_systems.models import NumberingSystem


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    metadata = models.JSONField(default=dict)
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="customers",
    )
    logo = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="customer_logo")
    default_billing_profile = models.OneToOneField(
        "BillingProfile",
        on_delete=models.PROTECT,
        related_name="+",
    )
    default_shipping_profile = models.OneToOneField(
        "ShippingProfile",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )
    billing_profiles = models.ManyToManyField("BillingProfile", related_name="customers")
    shipping_profiles = models.ManyToManyField("ShippingProfile", related_name="customers")

    objects = CustomerManager.from_queryset(CustomerQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        description: str | None,
        metadata: dict,
        logo: File | None,
    ) -> None:
        self.description = description
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
        address_data: dict | None,
    ) -> None:
        self.default_billing_profile.update(
            name=name,
            legal_name=legal_name,
            legal_number=legal_number,
            email=email,
            phone=phone,
        )
        self.default_billing_profile.address.update(**(address_data or {}))


class BillingProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="billing_profile_address",
    )
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES, null=True)
    language = models.CharField(max_length=10, null=True, choices=settings.LANGUAGES)
    net_payment_term = models.PositiveIntegerField(null=True)
    invoice_numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.PROTECT,
        related_name="invoice_numbering_billing_profiles",
        null=True,
    )
    credit_note_numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.PROTECT,
        related_name="credit_note_numbering_billing_profiles",
        null=True,
    )
    tax_rates = models.ManyToManyField(
        "tax_rates.TaxRate",
        through="BillingProfileTaxRate",
        related_name="billing_profiles",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="billing_profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    objects = BillingProfileManager.from_queryset(BillingProfileQuerySet)()

    def clone(self) -> BillingProfile:
        new_profile = BillingProfile.objects.create(
            name=self.name,
            legal_name=self.legal_name,
            legal_number=self.legal_number,
            email=self.email,
            phone=self.phone,
            address=Address.objects.from_address(self.address),
            currency=self.currency,
            language=self.language,
            net_payment_term=self.net_payment_term,
            invoice_numbering_system=self.invoice_numbering_system,
            credit_note_numbering_system=self.credit_note_numbering_system,
        )
        new_profile.tax_ids.set(self.tax_ids.clone())
        new_profile.tax_rates.set(self.tax_rates.all())
        return new_profile

    def update(
        self,
        name: str,
        legal_name: str | None,
        legal_number: str | None,
        email: str | None,
        phone: str | None,
        currency: str | None,
        language: str | None,
        net_payment_term: int | None,
        invoice_numbering_system: NumberingSystem | None,
        credit_note_numbering_system: NumberingSystem | None,
        address_data: dict | None,
    ) -> None:
        self.name = name
        self.legal_name = legal_name
        self.legal_number = legal_number
        self.email = email
        self.phone = phone
        self.currency = currency
        self.language = language
        self.net_payment_term = net_payment_term
        self.invoice_numbering_system = invoice_numbering_system
        self.credit_note_numbering_system = credit_note_numbering_system
        self.save()
        self.address.update(**(address_data or {}))


class BillingProfileTaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_profile = models.ForeignKey(
        "BillingProfile",
        on_delete=models.CASCADE,
        related_name="billing_profile_tax_rates",
    )
    tax_rate = models.ForeignKey(
        "tax_rates.TaxRate",
        on_delete=models.PROTECT,
        related_name="billing_profile_tax_rates",
    )

    class Meta:
        unique_together = ("billing_profile", "tax_rate")


class ShippingProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="shipping_profile_address",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    objects = ShippingProfileManager.from_queryset(ShippingProfileQuerySet)()

    def clone(self) -> ShippingProfile:
        return ShippingProfile.objects.create(
            name=self.name,
            phone=self.phone,
            address=Address.objects.from_address(self.address),
        )

    def update(
        self,
        name: str | None,
        phone: str | None,
        address_data: dict | None,
    ) -> None:
        self.name = name
        self.phone = phone
        self.save()
        self.address.update(**(address_data or {}))
