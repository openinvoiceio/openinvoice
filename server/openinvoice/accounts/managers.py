from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from openinvoice.addresses.models import Address
from openinvoice.core.utils import country_to_currency
from openinvoice.numbering_systems.models import NumberingSystem
from openinvoice.users.models import User

from .choices import MemberRole

if TYPE_CHECKING:
    from .models import BusinessProfile


class AccountManager(models.Manager):
    def create_account(
        self,
        name: str,
        email: str,
        country: str,
        business_profile: BusinessProfile,
        created_by: User,
        is_active: bool = True,
    ):
        account = self.create(
            name=name,
            email=email,
            country=country,
            default_currency=country_to_currency(country),
            language=settings.LANGUAGE_CODE,
            is_active=is_active,
            created_by=created_by,
            net_payment_term=settings.ACCOUNT_NET_PAYMENT_TERM,
            default_business_profile=business_profile,
        )
        account.business_profiles.add(business_profile)
        account.members.add(created_by, through_defaults={"role": MemberRole.OWNER})

        invoice_numbering_system = NumberingSystem.objects.create_default_invoice_numbering_system(
            account_id=account.id,
        )
        credit_note_numbering_system = NumberingSystem.objects.create_default_credit_note_numbering_system(
            account_id=account.id,
        )

        account.invoice_numbering_system = invoice_numbering_system
        account.credit_note_numbering_system = credit_note_numbering_system
        account.save(update_fields=["invoice_numbering_system", "credit_note_numbering_system", "updated_at"])

        return account


class BusinessProfileManager(models.Manager):
    def create_profile(
        self,
        legal_name: str | None = None,
        legal_number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address_data: dict | None = None,
    ):
        address = Address.objects.create_address(**(address_data or {}))
        return self.create(
            legal_name=legal_name,
            legal_number=legal_number,
            email=email,
            phone=phone,
            address=address,
        )
