import uuid
from unittest.mock import ANY

import pytest

from openinvoice.invoices.choices import InvoiceDeliveryMethod, InvoiceDocumentAudience, InvoiceStatus
from tests.factories import InvoiceDocumentFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_void_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    document = InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/void")

    assert response.status_code == 200
    invoice.refresh_from_db()
    document.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
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
            "invoice_numbering_system_id": invoice.billing_profile.invoice_numbering_system_id,
            "credit_note_numbering_system_id": invoice.billing_profile.credit_note_numbering_system_id,
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
        "metadata": invoice.metadata,
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_excluding_tax_amount": "0.00",
        "shipping_amount": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "0.00",
        "payment_provider": None,
        "payment_connection_id": None,
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": None,
        "paid_at": None,
        "voided_at": invoice.voided_at.isoformat().replace("+00:00", "Z"),
        "previous_revision_id": None,
        "documents": [
            {
                "id": str(document.id),
                "audience": document.audience,
                "language": document.language,
                "footer": document.footer,
                "memo": document.memo,
                "custom_fields": document.custom_fields,
                "url": None,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "lines": [],
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
        "shipping": None,
    }


def test_void_invoice_revision(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    revision = InvoiceFactory(
        head=invoice.head,
        account=account,
        customer=invoice.customer,
        previous_revision=invoice,
        status=InvoiceStatus.OPEN,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{revision.id}/void")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.VOIDED

    revision.refresh_from_db()
    assert revision.status == InvoiceStatus.VOIDED
    assert revision.voided_at is not None


@pytest.mark.parametrize("status", [InvoiceStatus.PAID, InvoiceStatus.VOIDED, InvoiceStatus.DRAFT])
def test_void_non_open_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/void")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only open invoices can be voided",
            }
        ],
    }


def test_void_invoice_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{uuid.uuid4()}/void")

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


def test_void_invoice_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{other_invoice.id}/void")

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


def test_void_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/invoices/{uuid.uuid4()}/void")

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


def test_void_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.post(f"/api/v1/invoices/{invoice.id}/void")

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
