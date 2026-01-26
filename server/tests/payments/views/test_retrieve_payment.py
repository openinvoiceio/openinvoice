import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from apps.invoices.choices import InvoiceStatus
from apps.payments.choices import PaymentStatus
from tests.factories import InvoiceFactory, PaymentFactory

pytestmark = pytest.mark.django_db


def test_retrieve_payment(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"))
    payment = PaymentFactory(account=account, currency=invoice.currency, amount=Decimal("10.00"))
    payment.invoices.add(invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/payments/{payment.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(payment.id),
        "status": PaymentStatus.SUCCEEDED,
        "currency": invoice.currency,
        "amount": "10.00",
        "description": payment.description,
        "transaction_id": payment.transaction_id,
        "url": None,
        "message": None,
        "invoice_ids": [invoice.id],
        "provider": None,
        "received_at": payment.received_at.isoformat().replace("+00:00", "Z"),
        "created_at": ANY,
    }


def test_retrieve_payment_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()
    payment = PaymentFactory(account=invoice.account)
    payment.invoices.add(invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/payments/{payment.id}")

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


def test_retrieve_payment_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    payment = PaymentFactory(account=account)
    payment.invoices.add(invoice)

    response = api_client.get(f"/api/v1/payments/{payment.id}")

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


def test_retrieve_payment_requires_account(api_client, user):
    invoice = InvoiceFactory()
    payment = PaymentFactory(account=invoice.account)
    payment.invoices.add(invoice)

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/payments/{payment.id}")

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


def test_retrieve_payment_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/payments/{uuid.uuid4()}")

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
