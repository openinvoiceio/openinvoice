import pytest

from apps.files.choices import FilePurpose
from apps.invoices.choices import InvoiceStatus
from tests.factories import (
    CustomerFactory,
    FileFactory,
    InvoiceFactory,
    PortalTokenFactory,
)

pytestmark = pytest.mark.django_db


def test_list_invoices_via_portal(api_client, account):
    customer = CustomerFactory(account=account)
    invoice1 = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)
    invoice2 = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.PAID)
    InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.get("/api/v1/portal/invoices", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(invoice.id),
                "number": invoice.number,
                "status": invoice.status,
                "currency": invoice.currency,
                "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
                "due_date": invoice.due_date.isoformat(),
                "total_amount": f"{invoice.total_amount.amount:.2f}",
                "pdf_url": None,
            }
            for invoice in [invoice2, invoice1]
        ],
    }


def test_list_invoices_with_pdf(api_client, account):
    customer = CustomerFactory(account=account)
    pdf = FileFactory(account=account, purpose=FilePurpose.INVOICE_PDF)
    invoice = InvoiceFactory(account=account, customer=customer, pdf=pdf, status=InvoiceStatus.PAID)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.get("/api/v1/portal/invoices", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert response.data == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(invoice.id),
                "number": invoice.number,
                "status": invoice.status,
                "currency": invoice.currency,
                "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
                "due_date": invoice.due_date.isoformat(),
                "total_amount": f"{invoice.total_amount.amount:.2f}",
                "pdf_url": invoice.pdf.data.url,
            }
        ],
    }


def test_list_invoices_voided_or_draft(api_client, account):
    customer = CustomerFactory(account=account)
    InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.DRAFT)
    InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.VOIDED)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.get("/api/v1/portal/invoices", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert response.data == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


def test_list_invoices_requires_authentication(api_client):
    response = api_client.get("/api/v1/portal/invoices")

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


def test_list_invoices_with_invalid_token(api_client, account):
    customer = CustomerFactory(account=account)
    InvoiceFactory(account=account, customer=customer)

    response = api_client.get("/api/v1/portal/invoices", HTTP_AUTHORIZATION="Bearer bad")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "authentication_failed",
                "detail": "Invalid token",
            }
        ],
    }
