from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account
    from openinvoice.addresses.models import Address
    from openinvoice.files.models import File
    from openinvoice.numbering_systems.models import NumberingSystem

    from .models import Customer


class CustomerManager(models.Manager):
    def create_customer(
        self,
        account: Account,
        name: str,
        address: Address,
        legal_name: str | None = None,
        legal_number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        description: str | None = None,
        currency: str | None = None,
        language: str | None = None,
        net_payment_term: int | None = None,
        invoice_numbering_system: NumberingSystem | None = None,
        credit_note_numbering_system: NumberingSystem | None = None,
        metadata: dict | None = None,
        logo: File | None = None,
    ) -> Customer:
        return self.create(
            account=account,
            name=name,
            legal_name=legal_name,
            legal_number=legal_number,
            email=email,
            phone=phone,
            description=description,
            currency=currency,
            language=language,
            net_payment_term=net_payment_term,
            invoice_numbering_system=invoice_numbering_system,
            credit_note_numbering_system=credit_note_numbering_system,
            metadata=metadata or {},
            address=address,
            logo=logo,
        )
