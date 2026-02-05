import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from openinvoice.core.choices import FeatureCode
from openinvoice.credit_notes.choices import CreditNoteDeliveryMethod, CreditNoteReason, CreditNoteStatus
from tests.factories import CreditNoteFactory, InvoiceFactory, NumberingSystemFactory

pytestmark = pytest.mark.django_db


def test_update_credit_note(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    credit_note = CreditNoteFactory(
        invoice=invoice,
        number="CN-1",
        subtotal_amount=Decimal("10.00"),
        total_amount_excluding_tax=Decimal("10.00"),
        total_amount=Decimal("10.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}",
        {
            "number": "CN-10",
            "numbering_system_id": None,
            "reason": CreditNoteReason.ORDER_CHANGE,
            "metadata": {"source": "support"},
        },
    )

    assert response.status_code == 200
    credit_note.refresh_from_db()
    assert credit_note.number == "CN-10"
    assert credit_note.reason == CreditNoteReason.ORDER_CHANGE
    assert credit_note.metadata == {"source": "support"}
    assert response.data == {
        "id": str(credit_note.id),
        "invoice_id": str(invoice.id),
        "status": credit_note.status,
        "reason": credit_note.reason,
        "number": credit_note.effective_number,
        "numbering_system_id": None,
        "currency": credit_note.currency,
        "issue_date": None,
        "metadata": {"source": "support"},
        "delivery_method": CreditNoteDeliveryMethod.MANUAL,
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
        "lines": [],
        "taxes": [],
        "tax_breakdown": [],
    }


def test_update_credit_note_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY: False}}}
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        number="CN-1",
        delivery_method=CreditNoteDeliveryMethod.MANUAL,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}", {"delivery_method": CreditNoteDeliveryMethod.AUTOMATIC}
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_update_credit_note_numbering_system_not_found(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}",
        {
            "number": None,
            "numbering_system_id": str(numbering_system_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_update_credit_note_numbering_system_mismatch(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")
    numbering_system = NumberingSystemFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}",
        {
            "number": None,
            "numbering_system_id": str(numbering_system.id),
            "reason": credit_note.reason,
            "metadata": {},
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system.id}" - object does not exist.',
            }
        ],
    }


def test_update_credit_note_cannot_modify_issued(api_client, user, account):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=CreditNoteStatus.ISSUED,
        number="CN-1",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}",
        {
            "number": "CN-2",
            "numbering_system_id": None,
            "reason": credit_note.reason,
            "metadata": {},
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot update issued credit note",
            }
        ],
    }


def test_update_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    response = api_client.put(
        f"/api/v1/credit-notes/{credit_note.id}",
        {
            "number": "CN-2",
            "numbering_system_id": None,
            "reason": credit_note.reason,
            "metadata": {},
        },
    )

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


def test_update_credit_note_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/credit-notes/{uuid.uuid4()}",
        {
            "number": "CN-1",
            "numbering_system_id": None,
            "reason": CreditNoteReason.OTHER,
            "metadata": {},
        },
    )

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
