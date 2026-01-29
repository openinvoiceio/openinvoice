from decimal import Decimal
from unittest.mock import ANY
from uuid import uuid4

import pytest

from openinvoice.invoices.choices import InvoiceStatus
from openinvoice.payments.choices import PaymentStatus
from openinvoice.payments.models import Payment
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_record_payment(api_client, user, account):
    invoice = InvoiceFactory(
        account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"), outstanding_amount=Decimal("10.00")
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice.id),
            "currency": invoice.currency,
            "amount": "10.00",
            "description": "ref",
        },
    )

    assert response.status_code == 201
    invoice.refresh_from_db()
    payment = Payment.objects.get(id=response.data["id"])
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.paid_at is not None
    assert response.data == {
        "id": str(payment.id),
        "status": PaymentStatus.SUCCEEDED,
        "currency": invoice.currency,
        "amount": "10.00",
        "description": "ref",
        "transaction_id": None,
        "url": None,
        "message": None,
        "invoices": [invoice.id],
        "provider": None,
        "received_at": payment.received_at.isoformat().replace("+00:00", "Z"),
        "created_at": ANY,
    }


@pytest.mark.parametrize("status", [InvoiceStatus.DRAFT, InvoiceStatus.VOIDED, InvoiceStatus.PAID])
def test_record_payment_invalid_status(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status, total_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice.id),
            "currency": invoice.currency,
            "amount": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "invalid",
                "detail": f"Cannot record payment for invoice in status {status}",
            }
        ],
    }


def test_record_payment_amount_exceeds_total(api_client, user, account):
    invoice = InvoiceFactory(
        account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"), outstanding_amount=Decimal("10.00")
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice.id),
            "currency": invoice.currency,
            "amount": "20.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "amount",
                "code": "invalid",
                "detail": "Payment amount exceeds outstanding amount",
            }
        ],
    }


def test_record_payment_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"))

    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice.id),
            "currency": invoice.currency,
            "amount": "10.00",
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


def test_record_payment_requires_account(api_client, user):
    invoice = InvoiceFactory()

    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice.id),
            "currency": invoice.currency,
            "amount": "10.00",
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


def test_record_payment_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(other_invoice.id),
            "currency": other_invoice.currency,
            "amount": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{other_invoice.id}" - object does not exist.',
            }
        ],
    }


def test_record_payment_invoice_not_found(api_client, user, account):
    invoice_id = uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/payments",
        {
            "invoice_id": str(invoice_id),
            "currency": account.default_currency,
            "amount": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{invoice_id}" - object does not exist.',
            }
        ],
    }
