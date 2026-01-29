import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from openinvoice.invoices.models import InvoiceAccount, InvoiceCustomer
from tests.factories import (
    AddressFactory,
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
)

pytestmark = pytest.mark.django_db


def _assign_invoice_snapshots(invoice):
    invoice.invoice_customer = InvoiceCustomer.objects.create(
        name=invoice.customer.name,
        legal_name=invoice.customer.legal_name,
        legal_number=invoice.customer.legal_number,
        email=invoice.customer.email,
        phone=invoice.customer.phone,
        description=invoice.customer.description,
        address=AddressFactory(),
        logo=None,
    )
    invoice.invoice_account = InvoiceAccount.objects.create(
        name=invoice.account.name,
        legal_name=invoice.account.legal_name,
        legal_number=invoice.account.legal_number,
        email=invoice.account.email,
        phone=invoice.account.phone,
        address=AddressFactory(),
        logo=None,
    )
    invoice.save(update_fields=["invoice_customer", "invoice_account"])


def test_retrieve_credit_note(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    _assign_invoice_snapshots(invoice)
    credit_note = CreditNoteFactory(
        invoice=invoice,
        number="CN-1",
        subtotal_amount=Decimal("25.00"),
        total_amount_excluding_tax=Decimal("25.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("25.00"),
    )
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        description="Refunded item",
        quantity=1,
        unit_amount=Decimal("25.00"),
        amount=Decimal("25.00"),
        total_amount_excluding_tax=Decimal("25.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("25.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}")

    assert response.status_code == 200
    credit_note.refresh_from_db()
    line.refresh_from_db()
    customer_snapshot = invoice.invoice_customer
    account_snapshot = invoice.invoice_account
    assert response.data == {
        "id": str(credit_note.id),
        "invoice_id": str(invoice.id),
        "status": credit_note.status,
        "reason": credit_note.reason,
        "number": credit_note.effective_number,
        "numbering_system_id": None,
        "currency": credit_note.currency,
        "issue_date": None,
        "metadata": credit_note.metadata,
        "delivery_method": credit_note.delivery_method,
        "recipients": [],
        "subtotal_amount": f"{credit_note.subtotal_amount.amount:.2f}",
        "total_amount_excluding_tax": f"{credit_note.total_amount_excluding_tax.amount:.2f}",
        "total_tax_amount": f"{credit_note.total_tax_amount.amount:.2f}",
        "total_amount": f"{credit_note.total_amount.amount:.2f}",
        "payment_provider": None,
        "payment_connection_id": None,
        "created_at": ANY,
        "updated_at": ANY,
        "issued_at": None,
        "voided_at": None,
        "pdf_id": None,
        "customer": {
            "id": str(customer_snapshot.id),
            "name": customer_snapshot.name,
            "legal_name": customer_snapshot.legal_name,
            "legal_number": customer_snapshot.legal_number,
            "email": customer_snapshot.email,
            "phone": customer_snapshot.phone,
            "description": customer_snapshot.description,
            "address": {
                "line1": customer_snapshot.address.line1,
                "line2": customer_snapshot.address.line2,
                "locality": customer_snapshot.address.locality,
                "state": customer_snapshot.address.state,
                "postal_code": customer_snapshot.address.postal_code,
                "country": str(customer_snapshot.address.country),
            },
            "logo_id": None,
            "tax_ids": [],
        },
        "account": {
            "id": str(account_snapshot.id),
            "name": account_snapshot.name,
            "legal_name": account_snapshot.legal_name,
            "legal_number": account_snapshot.legal_number,
            "email": account_snapshot.email,
            "phone": account_snapshot.phone,
            "address": {
                "line1": account_snapshot.address.line1,
                "line2": account_snapshot.address.line2,
                "locality": account_snapshot.address.locality,
                "state": account_snapshot.address.state,
                "postal_code": account_snapshot.address.postal_code,
                "country": str(account_snapshot.address.country),
            },
            "logo_id": None,
            "tax_ids": [],
        },
        "lines": [
            {
                "id": str(line.id),
                "invoice_line_id": str(line.invoice_line_id),
                "description": line.description,
                "quantity": line.quantity,
                "unit_amount": f"{line.unit_amount.amount:.2f}",
                "amount": f"{line.amount.amount:.2f}",
                "total_amount_excluding_tax": f"{line.total_amount_excluding_tax.amount:.2f}",
                "total_tax_amount": f"{line.total_tax_amount.amount:.2f}",
                "total_amount": f"{line.total_amount.amount:.2f}",
                "taxes": [],
            }
        ],
        "taxes": [],
        "tax_breakdown": [],
    }


def test_retrieve_credit_note_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}")

    assert response.status_code == 404
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_retrieve_credit_note_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/credit-notes/{uuid.uuid4()}")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }


def test_retrieve_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }
