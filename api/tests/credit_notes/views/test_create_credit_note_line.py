import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.choices import CreditNoteStatus
from tests.factories import CreditNoteFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_create_credit_note_line_from_invoice_line(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("30.00"),
        total_excluding_tax_amount=Decimal("30.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("30.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("30.00"),
        amount=Decimal("30.00"),
        total_excluding_tax_amount=Decimal("30.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("30.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "quantity": 1,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "invoice_line_id": str(invoice_line.id),
        "description": invoice_line.description,
        "quantity": 1,
        "unit_amount": "30.00",
        "amount": "30.00",
        "total_amount_excluding_tax": "30.00",
        "total_tax_amount": "0.00",
        "total_amount": "30.00",
        "taxes": [],
    }


def test_create_credit_note_line_from_invoice_line_using_amount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("15.00"),
        total_excluding_tax_amount=Decimal("15.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("15.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=3,
        unit_amount=Decimal("5.00"),
        amount=Decimal("15.00"),
        total_excluding_tax_amount=Decimal("15.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("15.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "amount": "10.00",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "invoice_line_id": str(invoice_line.id),
        "description": invoice_line.description,
        "quantity": None,
        "unit_amount": "5.00",
        "amount": "10.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.00",
        "total_amount": "10.00",
        "taxes": [],
    }


def test_create_credit_note_line_custom_line(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("100.00"))
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Manual adjustment",
            "quantity": 2,
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "invoice_line_id": None,
        "description": "Manual adjustment",
        "quantity": 2,
        "unit_amount": "5.00",
        "amount": "10.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.00",
        "total_amount": "10.00",
        "taxes": [],
    }


def test_create_credit_note_line_custom_line_ignores_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("100.00"))
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Manual adjustment",
            "quantity": 2,
            "unit_amount": "5.00",
            "amount": "5.00",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "invoice_line_id": None,
        "description": "Manual adjustment",
        "quantity": 2,
        "unit_amount": "5.00",
        "amount": "10.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.00",
        "total_amount": "10.00",
        "taxes": [],
    }


def test_create_credit_note_line_not_found(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Manual adjustment",
            "quantity": 1,
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "credit_note_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{credit_note.id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_line_invoice_line_not_found(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    invoice_line_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "invoice_line_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{invoice_line_id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_line_amount_exceeds_invoice(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Too large",
            "quantity": 1,
            "unit_amount": "20.00",
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


def test_create_credit_note_line_without_amount_or_quantity(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("12.00"),
        total_excluding_tax_amount=Decimal("12.00"),
        total_amount=Decimal("12.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=3,
        unit_amount=Decimal("4.00"),
        amount=Decimal("12.00"),
        total_excluding_tax_amount=Decimal("12.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("12.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "invoice_line_id": str(invoice_line.id),
        "description": invoice_line.description,
        "quantity": 3,
        "unit_amount": "4.00",
        "amount": "12.00",
        "total_amount_excluding_tax": "12.00",
        "total_tax_amount": "0.00",
        "total_amount": "12.00",
        "taxes": [],
    }


def test_create_credit_note_line_invoice_line_without_outstanding(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("5.00"),
        amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
        total_credit_amount=Decimal("10.00"),
        outstanding_amount=Decimal("0.00"),
        credit_quantity=2,
        outstanding_quantity=0,
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "quantity": 1,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Invoice line has no outstanding balance to credit",
            }
        ],
    }


def test_create_credit_note_line_requires_exclusive_amount_or_quantity(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("20.00"),
        total_excluding_tax_amount=Decimal("20.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("10.00"),
        amount=Decimal("20.00"),
        total_excluding_tax_amount=Decimal("20.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "quantity": 1,
            "amount": "5.00",
        },
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


def test_create_credit_note_line_amount_exceeds_outstanding(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("5.00"),
        amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
        total_credit_amount=Decimal("8.00"),
        outstanding_amount=Decimal("2.00"),
        credit_quantity=1,
        outstanding_quantity=1,
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "amount": "5.00",
        },
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


def test_create_credit_note_line_quantity_exceeds_outstanding(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("5.00"),
        amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
        credit_quantity=1,
        outstanding_quantity=1,
        total_credit_amount=Decimal("5.00"),
        outstanding_amount=Decimal("5.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "invoice_line_id": str(invoice_line.id),
            "quantity": 2,
        },
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


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_create_credit_note_line_cannot_modify_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-10",
    )

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Manual adjustment",
            "quantity": 1,
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "credit_note_id",
                "code": "invalid",
                "detail": "Cannot modify issued credit note",
            }
        ],
    }


def test_create_credit_note_line_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(credit_note.id),
            "description": "Manual adjustment",
            "quantity": 1,
            "unit_amount": "5.00",
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


def test_create_credit_note_line_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.post(
        "/api/v1/credit-note-lines",
        {
            "credit_note_id": str(uuid.uuid4()),
            "description": "Manual adjustment",
            "quantity": 1,
            "unit_amount": "5.00",
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
