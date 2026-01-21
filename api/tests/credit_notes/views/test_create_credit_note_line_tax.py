import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.choices import CreditNoteStatus
from apps.credit_notes.models import CreditNoteLine
from tests.factories import (
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_create_credit_note_line_tax(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=None,
        quantity=1,
        unit_amount=Decimal("10.00"),
        amount=Decimal("10.00"),
        total_amount_excluding_tax=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 201
    refreshed_line = CreditNoteLine.objects.get(id=line.id)
    assert response.data == {
        "id": str(refreshed_line.id),
        "invoice_line_id": None,
        "description": refreshed_line.description,
        "quantity": 1,
        "unit_amount": "10.00",
        "amount": "10.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.50",
        "total_amount": "10.50",
        "taxes": [
            {
                "id": str(refreshed_line.taxes.first().id),
                "tax_rate_id": str(tax_rate.id),
                "name": tax_rate.name,
                "description": tax_rate.description,
                "rate": str(tax_rate.percentage),
                "amount": "0.50",
            }
        ],
    }


def test_create_credit_note_line_tax_requires_authentication(api_client, account):
    line = CreditNoteLineFactory(
        credit_note=CreditNoteFactory(invoice=InvoiceFactory(account=account)),
        invoice_line=None,
    )

    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(uuid.uuid4())},
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


def test_create_credit_note_line_tax_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/credit-note-lines/{uuid.uuid4()}/taxes",
        {"tax_rate_id": str(uuid.uuid4())},
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


def test_create_credit_note_line_tax_rejects_foreign_account(api_client, user, account):
    line = CreditNoteLineFactory()
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

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


def test_create_credit_note_line_tax_manual_only(api_client, user, account):
    line = CreditNoteLineFactory(credit_note=CreditNoteFactory(invoice=InvoiceFactory(account=account)))
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Manual taxes can only be managed for custom lines",
            }
        ],
    }


def test_create_credit_note_line_tax_not_found(api_client, user, account):
    line = CreditNoteLineFactory(
        credit_note=CreditNoteFactory(invoice=InvoiceFactory(account=account)),
        invoice_line=None,
    )
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id}" - object does not exist.',
            }
        ],
    }


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_create_credit_note_line_tax_cannot_modify_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-20",
    )
    line = CreditNoteLineFactory(credit_note=credit_note, invoice_line=None)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-note-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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
