from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceDeliveryMethod, InvoiceStatus
from apps.invoices.models import Invoice
from tests.factories import CustomerFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_list_invoices(api_client, user, account):
    first_invoice = InvoiceFactory(account=account)
    second_invoice = InvoiceFactory(account=account)
    InvoiceFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(invoice.id),
                "status": invoice.status,
                "number": invoice.effective_number,
                "numbering_system_id": None,
                "previous_revision_id": None,
                "latest_revision_id": invoice.latest_revision_id,
                "currency": invoice.currency,
                "issue_date": None,
                "sell_date": None,
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
                "metadata": {},
                "custom_fields": {},
                "footer": None,
                "description": None,
                "delivery_method": InvoiceDeliveryMethod.MANUAL,
                "recipients": [],
                "subtotal_amount": "0.00",
                "total_discount_amount": "0.00",
                "total_amount_excluding_tax": "0.00",
                "total_tax_amount": "0.00",
                "total_amount": "0.00",
                "total_credit_amount": "0.00",
                "total_paid_amount": "0.00",
                "outstanding_amount": "0.00",
                "payment_provider": None,
                "created_at": ANY,
                "updated_at": ANY,
                "opened_at": None,
                "paid_at": None,
                "voided_at": None,
                "pdf_id": None,
                "lines": [],
                "taxes": [],
                "discounts": [],
                "tax_breakdown": [],
                "discount_breakdown": [],
            }
            for invoice in [second_invoice, first_invoice]
        ],
    }


def test_list_invoices_requires_authentication(api_client):
    response = api_client.get("/api/v1/invoices")

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


def test_list_invoices_with_line(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["lines"] == [
        {
            "id": str(line.id),
            "description": line.description,
            "quantity": 1,
            "unit_amount": "0.00",
            "price_id": None,
            "product_id": None,
            "amount": "0.00",
            "total_discount_amount": "0.00",
            "total_amount_excluding_tax": "0.00",
            "total_tax_amount": "0.00",
            "total_tax_rate": "0.00",
            "total_amount": "0.00",
            "total_credit_amount": "0.00",
            "outstanding_amount": "0.00",
            "credit_quantity": 0,
            "outstanding_quantity": 1,
            "discounts": [],
            "taxes": [],
        }
    ]


def test_list_invoices_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/invoices")

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


def test_list_invoices_filter_by_status(api_client, user, account):
    InvoiceFactory(account=account, status=InvoiceStatus.DRAFT)
    paid_invoice = InvoiceFactory(account=account, status=InvoiceStatus.PAID)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"status": "paid"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(paid_invoice.id)]


def test_list_invoices_filter_by_customer_id(api_client, user, account):
    customer1 = CustomerFactory(account=account)
    invoice1 = InvoiceFactory(account=account, customer=customer1)
    customer2 = CustomerFactory(account=account)
    InvoiceFactory(account=account, customer=customer2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"customer_id": str(customer1.id)})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(invoice1.id)]


def test_list_invoices_filter_by_currency(api_client, user, account):
    usd_invoice = InvoiceFactory(account=account, currency="USD")
    InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"currency": "USD"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(usd_invoice.id)]


def test_list_invoices_filter_by_created_at_after(api_client, user, account):
    base = timezone.now()
    older = InvoiceFactory(account=account)
    Invoice.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/invoices",
        {"created_at_after": (base - timedelta(hours=12)).isoformat()},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_invoices_filter_by_created_at_before(api_client, user, account):
    base = timezone.now()
    older = InvoiceFactory(account=account)
    Invoice.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_invoices_search_by_number(api_client, user, account):
    invoice = InvoiceFactory(account=account, number="INV-1")
    InvoiceFactory(account=account, number="INV-2")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"search": "INV-1"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(invoice.id)]


def test_list_invoices_order_by_created_at(api_client, user, account):
    base = timezone.now()
    older = InvoiceFactory(account=account)
    Invoice.objects.filter(id=older.id).update(created_at=base - timedelta(seconds=1))
    newer = InvoiceFactory(account=account)
    Invoice.objects.filter(id=newer.id).update(created_at=base)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"ordering": "created_at"})

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert [r["id"] for r in response.data["results"]] == [
        str(older.id),
        str(newer.id),
    ]


def test_list_invoices_order_by_created_at_desc(api_client, user, account):
    base = timezone.now()
    older = InvoiceFactory(account=account)
    Invoice.objects.filter(id=older.id).update(created_at=base - timedelta(seconds=1))
    newer = InvoiceFactory(account=account)
    Invoice.objects.filter(id=newer.id).update(created_at=base)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invoices", {"ordering": "-created_at"})

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert [r["id"] for r in response.data["results"]] == [
        str(newer.id),
        str(older.id),
    ]
