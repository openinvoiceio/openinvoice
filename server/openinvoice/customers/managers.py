from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from openinvoice.addresses.models import Address

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account
    from openinvoice.files.models import File
    from openinvoice.numbering_systems.models import NumberingSystem

    from .models import BillingProfile, Customer, ShippingProfile


class CustomerManager(models.Manager):
    def create_customer(
        self,
        account: Account,
        name: str,
        default_billing_profile: BillingProfile,
        description: str | None = None,
        metadata: dict | None = None,
        logo: File | None = None,
        default_shipping_profile: ShippingProfile | None = None,
    ) -> Customer:
        return self.create(
            account=account,
            name=name,
            description=description,
            metadata=metadata or {},
            logo=logo,
            default_billing_profile=default_billing_profile,
            default_shipping_profile=default_shipping_profile,
        )


class BillingProfileManager(models.Manager):
    def create_profile(
        self,
        legal_name: str | None = None,
        legal_number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address_data: dict | None = None,
        currency: str | None = None,
        language: str | None = None,
        net_payment_term: int | None = None,
        invoice_numbering_system: NumberingSystem | None = None,
        credit_note_numbering_system: NumberingSystem | None = None,
    ) -> BillingProfile:
        address = Address.objects.create_address(**(address_data or {}))
        return self.create(
            legal_name=legal_name,
            legal_number=legal_number,
            email=email,
            phone=phone,
            address=address,
            currency=currency,
            language=language,
            net_payment_term=net_payment_term,
            invoice_numbering_system=invoice_numbering_system,
            credit_note_numbering_system=credit_note_numbering_system,
        )


class ShippingProfileManager(models.Manager):
    def create_profile(
        self,
        name: str | None = None,
        phone: str | None = None,
        address_data: dict | None = None,
    ) -> ShippingProfile:
        address = Address.objects.create_address(**(address_data or {}))
        return self.create(
            name=name,
            phone=phone,
            address=address,
        )
