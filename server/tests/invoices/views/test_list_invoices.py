from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone

from openinvoice.invoices.choices import InvoiceDeliveryMethod, InvoiceDocumentAudience, InvoiceStatus
from openinvoice.invoices.models import Invoice
from tests.factories import CustomerFactory, InvoiceDocumentFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_list_invoices(api_client, user, account):
    first_invoice = InvoiceFactory(account=account)
    second_invoice = InvoiceFactory(account=account)
    first_document = InvoiceDocumentFactory(invoice=first_invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    second_document = InvoiceDocumentFactory(invoice=second_invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
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
                "currency": invoice.currency,
                "tax_behavior": invoice.tax_behavior,
                "issue_date": None,
                "due_date": invoice.due_date.isoformat(),
                "net_payment_term": invoice.net_payment_term,
                "billing_profile": {
                    "id": str(invoice.billing_profile.id),
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
                "metadata": {},
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
                "voided_at": None,
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
            for invoice, document in zip(
                [second_invoice, first_invoice],
                [second_document, first_document],
                strict=False,
            )
        ],
    }


def test_list_invoices_requires_authentication(api_client):
    response = api_client.get("/api/v1/invoices")

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
            "subtotal_amount": "0.00",
            "total_discount_amount": "0.00",
            "total_excluding_tax_amount": "0.00",
            "total_tax_amount": "0.00",
            "total_tax_rate": "0.00",
            "total_amount": "0.00",
            "total_credit_amount": "0.00",
            "outstanding_amount": "0.00",
            "credit_quantity": 0,
            "outstanding_quantity": 1,
            "coupons": [],
            "discounts": [],
            "total_discounts": [],
            "tax_rates": [],
            "taxes": [],
            "total_taxes": [],
        }
    ]


def test_list_invoices_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/invoices")

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
