import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.choices import InvoiceDeliveryMethod, InvoiceStatus
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_void_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/void")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "issue_date": invoice.issue_date,
        "sell_date": invoice.sell_date,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "customer": {
            "id": str(invoice.customer.id),
            "name": invoice.customer.name,
            "legal_name": invoice.customer.legal_name,
            "legal_number": invoice.customer.legal_number,
            "email": invoice.customer.email,
            "phone": invoice.customer.phone,
            "description": invoice.customer.description,
            "billing_address": {
                "line1": invoice.customer.billing_address.line1,
                "line2": invoice.customer.billing_address.line2,
                "locality": invoice.customer.billing_address.locality,
                "state": invoice.customer.billing_address.state,
                "postal_code": invoice.customer.billing_address.postal_code,
                "country": invoice.customer.billing_address.country,
            },
            "shipping_address": {
                "line1": invoice.customer.shipping_address.line1,
                "line2": invoice.customer.shipping_address.line2,
                "locality": invoice.customer.shipping_address.locality,
                "state": invoice.customer.shipping_address.state,
                "postal_code": invoice.customer.shipping_address.postal_code,
                "country": invoice.customer.shipping_address.country,
            },
            "logo_id": None,
        },
        "account": {
            "id": str(invoice.account.id),
            "name": invoice.account.name,
            "legal_name": invoice.account.legal_name,
            "legal_number": invoice.account.legal_number,
            "email": invoice.account.email,
            "phone": invoice.account.phone,
            "address": {
                "line1": invoice.account.address.line1,
                "line2": invoice.account.address.line2,
                "locality": invoice.account.address.locality,
                "state": invoice.account.address.state,
                "postal_code": invoice.account.address.postal_code,
                "country": invoice.account.address.country,
            },
            "logo_id": None,
        },
        "metadata": invoice.metadata,
        "custom_fields": invoice.custom_fields,
        "footer": invoice.footer,
        "description": invoice.description,
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
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
        "pdf_id": None,
        "lines": [],
        "coupons": [],
        "discounts": [],
        "tax_rates": [],
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
        "type": ErrorType.CLIENT_ERROR,
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
        "type": ErrorType.CLIENT_ERROR,
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
        "type": ErrorType.CLIENT_ERROR,
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
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }
