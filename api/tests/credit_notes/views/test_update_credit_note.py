import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.enums import CreditNoteDeliveryMethod, CreditNoteReason, CreditNoteStatus
from apps.invoices.models import InvoiceAccount, InvoiceCustomer
from common.enums import FeatureCode
from tests.factories import (
    AddressFactory,
    CreditNoteFactory,
    InvoiceFactory,
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def _assign_invoice_snapshots(invoice):
    invoice.customer_on_invoice = InvoiceCustomer.objects.create(
        name=invoice.customer.name,
        legal_name=invoice.customer.legal_name,
        legal_number=invoice.customer.legal_number,
        email=invoice.customer.email,
        phone=invoice.customer.phone,
        description=invoice.customer.description,
        billing_address=AddressFactory(),
        shipping_address=AddressFactory(),
        logo=None,
    )
    invoice.account_on_invoice = InvoiceAccount.objects.create(
        name=invoice.account.name,
        legal_name=invoice.account.legal_name,
        legal_number=invoice.account.legal_number,
        email=invoice.account.email,
        phone=invoice.account.phone,
        address=AddressFactory(),
        logo=None,
    )
    invoice.save(update_fields=["customer_on_invoice", "account_on_invoice"])


def test_update_credit_note(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    _assign_invoice_snapshots(invoice)
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
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    credit_note.refresh_from_db()
    assert credit_note.number == "CN-10"
    assert credit_note.reason == CreditNoteReason.ORDER_CHANGE
    assert credit_note.metadata == {"source": "support"}
    assert credit_note.description == "Updated description"
    customer_snapshot = invoice.customer_on_invoice
    account_snapshot = invoice.account_on_invoice
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
        "description": "Updated description",
        "delivery_method": CreditNoteDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": f"{credit_note.subtotal_amount.amount:.2f}",
        "total_amount_excluding_tax": f"{credit_note.total_amount_excluding_tax.amount:.2f}",
        "total_tax_amount": f"{credit_note.total_tax_amount.amount:.2f}",
        "total_amount": f"{credit_note.total_amount.amount:.2f}",
        "payment_provider": None,
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
            "billing_address": {
                "line1": customer_snapshot.billing_address.line1,
                "line2": customer_snapshot.billing_address.line2,
                "locality": customer_snapshot.billing_address.locality,
                "state": customer_snapshot.billing_address.state,
                "postal_code": customer_snapshot.billing_address.postal_code,
                "country": str(customer_snapshot.billing_address.country),
            },
            "shipping_address": {
                "line1": customer_snapshot.shipping_address.line1,
                "line2": customer_snapshot.shipping_address.line2,
                "locality": customer_snapshot.shipping_address.locality,
                "state": customer_snapshot.shipping_address.state,
                "postal_code": customer_snapshot.shipping_address.postal_code,
                "country": str(customer_snapshot.shipping_address.country),
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
        "type": ErrorType.VALIDATION_ERROR,
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
        "type": ErrorType.VALIDATION_ERROR,
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
            "description": credit_note.description,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
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
            "description": credit_note.description,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
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
            "description": credit_note.description,
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


def test_update_credit_note_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/credit-notes/{uuid.uuid4()}",
        {
            "number": "CN-1",
            "numbering_system_id": None,
            "reason": CreditNoteReason.OTHER,
            "metadata": {},
            "description": None,
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
