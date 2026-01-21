import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.choices import CreditNoteStatus
from tests.factories import CreditNoteFactory, CreditNoteLineFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_update_credit_note_line_manual_line(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal(100))
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("5.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=None,
        description="Manual",
        quantity=1,
        unit_amount=Decimal("5.00"),
        amount=Decimal("5.00"),
        total_amount_excluding_tax=Decimal("5.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("5.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {
            "description": "Updated manual",
            "quantity": 2,
            "unit_amount": "7.50",
        },
    )

    assert response.status_code == 200
    line.refresh_from_db()
    assert line.description == "Updated manual"
    assert line.quantity == 2
    assert response.data == {
        "id": str(line.id),
        "invoice_line_id": None,
        "description": "Updated manual",
        "quantity": 2,
        "unit_amount": "7.50",
        "amount": "15.00",
        "total_amount_excluding_tax": "15.00",
        "total_tax_amount": "0.00",
        "total_amount": "15.00",
        "taxes": [],
    }


def test_update_credit_note_line_from_invoice_line(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("24.00"))
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("12.00"),
        amount=Decimal("24.00"),
        total_amount_excluding_tax=Decimal("24.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("24.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("12.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("12.00"),
        amount=Decimal("12.00"),
        total_amount=Decimal("12.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"quantity": 2},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "invoice_line_id": str(invoice_line.id),
        "description": invoice_line.description,
        "quantity": 2,
        "unit_amount": "12.00",
        "amount": "24.00",
        "total_amount_excluding_tax": "24.00",
        "total_tax_amount": "0.00",
        "total_amount": "24.00",
        "taxes": [],
    }


def test_update_credit_note_line_from_invoice_line_using_amount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        total_amount=Decimal("24.00"),
        total_credit_amount=Decimal("12.00"),
        outstanding_amount=Decimal("12.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("12.00"),
        amount=Decimal("24.00"),
        total_amount_excluding_tax=Decimal("24.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("24.00"),
        total_credit_amount=Decimal("12.00"),
        outstanding_amount=Decimal("12.00"),
        credit_quantity=1,
        outstanding_quantity=1,
    )
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("12.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("12.00"),
        amount=Decimal("12.00"),
        total_amount=Decimal("12.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"amount": "6.00"},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "invoice_line_id": str(invoice_line.id),
        "description": invoice_line.description,
        "quantity": None,
        "unit_amount": "12.00",
        "amount": "6.00",
        "total_amount_excluding_tax": "6.00",
        "total_tax_amount": "0.00",
        "total_amount": "6.00",
        "taxes": [],
    }


def test_update_credit_note_line_amount_exceeds_outstanding(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("20.00"))
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("10.00"),
        amount=Decimal("20.00"),
        total_amount_excluding_tax=Decimal("20.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
        total_credit_amount=Decimal("15.00"),
        outstanding_amount=Decimal("5.00"),
        credit_quantity=1,
        outstanding_quantity=1,
    )
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("5.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=None,
        unit_amount=Decimal("10.00"),
        amount=Decimal("5.00"),
        total_amount=Decimal("5.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"amount": "10.00"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "amount",
                "code": "invalid",
                "detail": "Amount exceeds the outstanding amount",
            }
        ],
    }


def test_update_credit_note_line_amount_exceeds_invoice(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("20.00"),
        total_amount_excluding_tax=Decimal("20.00"),
        total_amount=Decimal("20.00"),
        total_credit_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
    )
    credit_note = CreditNoteFactory(
        invoice=invoice,
        total_amount=Decimal("10.00"),
    )
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=None,
        quantity=1,
        unit_amount=Decimal("10.00"),
        amount=Decimal("10.00"),
        total_amount_excluding_tax=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {
            "quantity": 2,
            "unit_amount": "15.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Credit note amount exceeds the invoice balance",
            }
        ],
    }


def test_update_credit_note_line_quantity_exceeds_outstanding(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("20.00"))
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("10.00"),
        amount=Decimal("20.00"),
        total_amount_excluding_tax=Decimal("20.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
        total_credit_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
        credit_quantity=1,
        outstanding_quantity=1,
    )
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("10.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("10.00"),
        amount=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"quantity": 2},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "quantity",
                "code": "invalid",
                "detail": "Quantity exceeds the outstanding quantity",
            }
        ],
    }


def test_update_credit_note_line_requires_exclusive_amount_or_quantity(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("24.00"))
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("12.00"),
        amount=Decimal("24.00"),
        total_amount_excluding_tax=Decimal("24.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("24.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("12.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("12.00"),
        amount=Decimal("12.00"),
        total_amount=Decimal("12.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"quantity": 1, "amount": "6.00"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Provide either quantity or amount for invoice lines",
            }
        ],
    }


def test_update_credit_note_line_custom_line_rejects_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("30.00"))
    credit_note = CreditNoteFactory(invoice=invoice, total_amount=Decimal("5.00"))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=None,
        quantity=1,
        unit_amount=Decimal("5.00"),
        amount=Decimal("5.00"),
        total_amount=Decimal("5.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {"amount": "3.00"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "amount",
                "code": "invalid",
                "detail": "Amount can only be set for invoice lines",
            }
        ],
    }


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_update_credit_note_line_cannot_modify_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-60",
    )
    line = CreditNoteLineFactory(credit_note=credit_note, invoice_line=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {
            "quantity": 2,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot modify issued credit note",
            }
        ],
    }


def test_update_credit_note_line_requires_authentication(api_client, account):
    line = CreditNoteLineFactory(credit_note=CreditNoteFactory(invoice=InvoiceFactory(account=account)))

    response = api_client.put(
        f"/api/v1/credit-note-lines/{line.id}",
        {
            "quantity": 1,
        },
    )

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


def test_update_credit_note_line_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/credit-note-lines/{uuid.uuid4()}",
        {
            "quantity": 1,
        },
    )

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
