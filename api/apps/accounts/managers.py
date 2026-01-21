from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.addresses.models import Address
from apps.numbering_systems.models import NumberingSystem
from apps.users.models import User
from common.utils import country_to_currency

from .choices import MemberRole
from .querysets import AccountQuerySet, InvitationQuerySet


class AccountManager(models.Manager.from_queryset(AccountQuerySet)):  # type: ignore[misc]
    def create_account(
        self,
        name: str,
        country: str,
        email: str,
        created_by: User,
        legal_name: str | None = None,
        legal_number: str | None = None,
        is_active: bool = True,
    ):
        address = Address.objects.create_address()

        account = self.create(
            name=name,
            legal_name=legal_name,
            legal_number=legal_number,
            email=email,
            country=country,
            default_currency=country_to_currency(country),
            is_active=is_active,
            created_by=created_by,
            address=address,
            net_payment_term=settings.ACCOUNT_NET_PAYMENT_TERM,
        )

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


class InvitationManager(models.Manager.from_queryset(InvitationQuerySet)):
    pass
