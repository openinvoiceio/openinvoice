import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from tests.factories import CreditNoteFactory, CreditNoteLineFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_retrieve_credit_note(api_client, user, account):
    invoice = InvoiceFactory(account=account)
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
        "billing_profile": {
            "id": str(invoice.billing_profile.id),
            "name": invoice.billing_profile.name,
            "legal_name": invoice.billing_profile.legal_name,
            "legal_number": invoice.billing_profile.legal_number,
            "email": invoice.billing_profile.email,
            "phone": invoice.billing_profile.phone,
            "address": {
                "line1": invoice.billing_profile.address.line1,
                "line2": invoice.billing_profile.address.line2,
                "locality": invoice.billing_profile.address.locality,
                "state": invoice.billing_profile.address.state,
                "postal_code": invoice.billing_profile.address.postal_code,
                "country": str(invoice.billing_profile.address.country),
            },
            "currency": invoice.billing_profile.currency,
            "language": invoice.billing_profile.language,
            "net_payment_term": invoice.billing_profile.net_payment_term,
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "business_profile": {
            "id": str(invoice.business_profile.id),
            "name": invoice.business_profile.name,
            "legal_name": invoice.business_profile.legal_name,
            "legal_number": invoice.business_profile.legal_number,
            "email": invoice.business_profile.email,
            "phone": invoice.business_profile.phone,
            "address": {
                "line1": invoice.business_profile.address.line1,
                "line2": invoice.business_profile.address.line2,
                "locality": invoice.business_profile.address.locality,
                "state": invoice.business_profile.address.state,
                "postal_code": invoice.business_profile.address.postal_code,
                "country": str(invoice.business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
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
