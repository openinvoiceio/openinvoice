import uuid
from decimal import Decimal

import pytest
from djmoney.money import Money
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.choices import CreditNoteStatus
from apps.invoices.choices import InvoiceStatus
from tests.factories import (
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
    InvoiceLineFactory,
)

pytestmark = pytest.mark.django_db


def test_void_credit_note(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("100.00"),
        total_excluding_tax_amount=Decimal("100.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        total_credit_amount=Decimal("0.00"),
        outstanding_amount=Decimal("100.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("50.00"),
        amount=Decimal("100.00"),
        total_excluding_tax_amount=Decimal("100.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        total_credit_amount=Decimal("0.00"),
        credit_quantity=0,
        outstanding_amount=Decimal("100.00"),
        outstanding_quantity=2,
    )
    credit_note = CreditNoteFactory(
        number="CN-1",
        invoice=invoice,
        status=CreditNoteStatus.ISSUED,
        subtotal_amount=Decimal("50.00"),
        total_amount_excluding_tax=Decimal("50.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("50.00"),
    )
    CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("50.00"),
        amount=Decimal("50.00"),
        total_amount_excluding_tax=Decimal("50.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("50.00"),
    )

    invoice.recalculate_credit()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note.id}/void",
        {"reason": "Customer request"},
    )

    assert response.status_code == 200
    credit_note.refresh_from_db()
    assert credit_note.status == CreditNoteStatus.VOIDED
    assert response.data["status"] == CreditNoteStatus.VOIDED
    invoice.refresh_from_db()
    invoice_line.refresh_from_db()
    assert invoice.total_credit_amount == Money("0.00", invoice.currency)
    assert invoice.outstanding_amount == Money("100.00", invoice.currency)
    assert invoice_line.total_credit_amount == Money("0.00", invoice_line.currency)
    assert invoice_line.outstanding_amount == Money("100.00", invoice_line.currency)
    assert invoice_line.credit_quantity == 0
    assert invoice_line.outstanding_quantity == 2


def test_void_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/void")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_void_credit_note_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/credit-notes/{uuid.uuid4()}/void")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }


def test_void_credit_note_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/void")

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_void_credit_note_already_voided(api_client, user, account):
    credit_note = CreditNoteFactory(
        number="CN-1",
        invoice=InvoiceFactory(account=account),
        status=CreditNoteStatus.VOIDED,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/void")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Credit note already voided",
            }
        ],
    }


def test_void_credit_note_blocked_for_paid_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.PAID)
    credit_note = CreditNoteFactory(invoice=invoice, status=CreditNoteStatus.ISSUED, number="CN-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note.id}/void",
        {"reason": "Customer request"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot void credit note for paid invoice",
            }
        ],
    }
