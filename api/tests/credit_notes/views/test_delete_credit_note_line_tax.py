import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.enums import CreditNoteStatus
from apps.credit_notes.models import CreditNoteTax
from tests.factories import (
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_delete_credit_note_line_tax(api_client, user, account):
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
    credit_note_tax = CreditNoteTax.objects.create(
        credit_note=credit_note,
        credit_note_line=line,
        tax_rate=tax_rate,
        name=tax_rate.name,
        description=tax_rate.description,
        rate=tax_rate.percentage,
        currency=credit_note.currency,
        amount=Decimal("0.50"),
    )
    line.total_tax_amount = Decimal("0.50")
    line.total_amount = Decimal("10.50")
    line.save(update_fields=["total_tax_amount", "total_amount"])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}/taxes/{credit_note_tax.id}")

    assert response.status_code == 204
    assert CreditNoteTax.objects.count() == 0


def test_delete_credit_note_line_tax_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    line = CreditNoteLineFactory(credit_note=credit_note, invoice_line=None)
    tax_rate = TaxRateFactory(account=account)
    credit_note_tax = CreditNoteTax.objects.create(
        credit_note=credit_note,
        credit_note_line=line,
        tax_rate=tax_rate,
        name=tax_rate.name,
        description=tax_rate.description,
        rate=tax_rate.percentage,
        currency=credit_note.currency,
        amount=Decimal("0.50"),
    )

    response = api_client.delete(
        f"/api/v1/credit-note-lines/{credit_note_tax.credit_note_line_id}/taxes/{credit_note_tax.id}"
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


def test_delete_credit_note_line_tax_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/credit-note-lines/{uuid.uuid4()}/taxes/{uuid.uuid4()}")

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


def test_delete_credit_note_line_tax_rejects_foreign_account(api_client, user, account):
    credit_note_tax = CreditNoteTax.objects.create(
        credit_note=CreditNoteFactory(),
        credit_note_line=CreditNoteLineFactory(),
        tax_rate=TaxRateFactory(account=account),
        name="VAT",
        description="Tax",
        rate=Decimal("5.00"),
        currency="PLN",
        amount=Decimal("0.50"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(
        f"/api/v1/credit-note-lines/{credit_note_tax.credit_note_line_id}/taxes/{credit_note_tax.id}"
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


def test_delete_credit_note_line_tax_manual_only(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    credit_note = CreditNoteFactory(invoice=invoice)
    invoice_line = InvoiceLineFactory(invoice=invoice)
    line = CreditNoteLineFactory(credit_note=credit_note, invoice_line=invoice_line)
    tax_rate = TaxRateFactory(account=account)
    credit_note_tax = CreditNoteTax.objects.create(
        credit_note=credit_note,
        credit_note_line=line,
        tax_rate=tax_rate,
        name=tax_rate.name,
        description=tax_rate.description,
        rate=tax_rate.percentage,
        currency=credit_note.currency,
        amount=Decimal("1.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}/taxes/{credit_note_tax.id}")

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


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_delete_credit_note_line_tax_cannot_modify_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-50",
    )
    line = CreditNoteLineFactory(credit_note=credit_note, invoice_line=None)
    tax_rate = TaxRateFactory(account=account)
    credit_note_tax = CreditNoteTax.objects.create(
        credit_note=credit_note,
        credit_note_line=line,
        tax_rate=tax_rate,
        name=tax_rate.name,
        description=tax_rate.description,
        rate=tax_rate.percentage,
        currency=credit_note.currency,
        amount=Decimal("1.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}/taxes/{credit_note_tax.id}")

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
