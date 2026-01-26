from decimal import Decimal
from unittest.mock import ANY

import pytest

from apps.invoices.choices import InvoiceStatus
from tests.factories import InvoiceFactory, PaymentFactory

pytestmark = pytest.mark.django_db


def test_list_payments(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"))
    payment = PaymentFactory(account=account, currency=invoice.currency, amount=Decimal("10.00"))
    payment.invoices.add(invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/payments")

    assert response.status_code == 200
    assert response.data == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(payment.id),
                "status": payment.status,
                "currency": invoice.currency,
                "amount": "10.00",
                "description": payment.description,
                "transaction_id": payment.transaction_id,
                "url": None,
                "message": None,
                "invoice_ids": [invoice.id],
                "provider": payment.provider,
                "received_at": payment.received_at.isoformat().replace("+00:00", "Z"),
                "created_at": ANY,
            }
        ],
    }


def test_list_payments_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("5.00"))
    owned_payment = PaymentFactory(account=account, currency=invoice.currency, amount=Decimal("5.00"))
    owned_payment.invoices.add(invoice)
    PaymentFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/payments")

    assert response.status_code == 200
    assert [payment["id"] for payment in response.data["results"]] == [str(owned_payment.id)]


def test_list_payments_filter_by_invoice(api_client, user, account):
    invoice1 = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("5.00"))
    invoice2 = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("7.00"))
    payment1 = PaymentFactory(account=account, currency=invoice1.currency, amount=Decimal("5.00"))
    payment1.invoices.add(invoice1)
    payment2 = PaymentFactory(account=account, currency=invoice2.currency, amount=Decimal("7.00"))
    payment2.invoices.add(invoice2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/payments", {"invoice_id": invoice1.id})

    assert response.status_code == 200
    assert [res["id"] for res in response.data["results"]] == [str(payment1.id)]


def test_list_payments_filter_by_invoice_id(api_client, user, account):
    invoice1 = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("5.00"))
    invoice2 = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("7.00"))
    payment1 = PaymentFactory(account=account, currency=invoice1.currency, amount=Decimal("5.00"))
    payment1.invoices.add(invoice1)
    payment2 = PaymentFactory(account=account, currency=invoice2.currency, amount=Decimal("7.00"))
    payment2.invoices.add(invoice2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/payments", {"invoice_id": invoice1.id})

    assert response.status_code == 200
    assert [res["id"] for res in response.data["results"]] == [str(payment1.id)]


def test_list_payments_requires_authentication(api_client):
    response = api_client.get("/api/v1/payments")

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


def test_list_payments_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/payments")

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
