import uuid
from decimal import Decimal

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.enums import CreditNoteDeliveryMethod, CreditNoteStatus
from apps.invoices.enums import InvoiceStatus
from tests.factories import (
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
    StripeSubscriptionFactory,
)

pytestmark = pytest.mark.django_db


def test_issue_credit_note(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        total_amount=Decimal("20.00"),
        subtotal_amount=Decimal("20.00"),
        total_amount_excluding_tax=Decimal("20.00"),
    )
    credit_note = CreditNoteFactory(invoice=invoice, number="CN-1")
    CreditNoteLineFactory(credit_note=credit_note, invoice_line=None, amount=Decimal("20.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note.id}/issue",
        {"issue_date": timezone.now().date().isoformat()},
    )

    assert response.status_code == 200
    credit_note.refresh_from_db()
    assert credit_note.status == CreditNoteStatus.ISSUED
    assert credit_note.pdf_id is not None
    assert response.data["status"] == CreditNoteStatus.ISSUED
    assert response.data["pdf_id"] == str(credit_note.pdf_id)


def test_issue_credit_note_with_automatic_delivery_method(api_client, user, account, mailoutbox):
    StripeSubscriptionFactory(stripe_customer__account=account)
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    credit_note = CreditNoteFactory(
        invoice=invoice, number="CN-1", delivery_method=CreditNoteDeliveryMethod.AUTOMATIC, recipients=["a@example.com"]
    )
    CreditNoteLineFactory(credit_note=credit_note, invoice_line=None, amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to == ["a@example.com"]
    assert email.attachments[0][0] == f"{credit_note.effective_number}.pdf"


def test_issue_credit_note_automatic_without_recipients(api_client, user, account, mailoutbox):
    StripeSubscriptionFactory(stripe_customer__account=account)
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    credit_note = CreditNoteFactory(
        invoice=invoice, number="CN-1", delivery_method=CreditNoteDeliveryMethod.AUTOMATIC, recipients=[]
    )
    CreditNoteLineFactory(credit_note=credit_note, invoice_line=None, amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

    assert response.status_code == 200
    assert len(mailoutbox) == 0


def test_issue_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

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


def test_issue_credit_note_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.post(f"/api/v1/credit-notes/{uuid.uuid4()}/issue")

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


def test_issue_credit_note_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory(number="CN-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

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


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_issue_credit_note_not_draft(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        number="CN-1",
        status=status,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Credit note already issued",
            }
        ],
    }


def test_issue_credit_note_number_missing(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number=None)
    CreditNoteLineFactory(credit_note=credit_note, invoice_line=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Credit note number is required before issuing",
            }
        ],
    }


def test_issue_credit_note_requires_lines(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/credit-notes/{credit_note.id}/issue")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Credit note must contain at least one line",
            }
        ],
    }
