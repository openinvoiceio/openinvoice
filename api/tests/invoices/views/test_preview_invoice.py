import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.choices import InvoiceStatus
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_preview_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/preview")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "Invoice" in response.content.decode()


def test_preview_invoice_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{other_invoice.id}/preview")

    assert response.status_code == 404


def test_preview_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}/preview")

    assert response.status_code == 403


def test_preview_invoice_format_email(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/preview", {"format": "email"})

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert f"Hi {invoice.customer.name}" in response.content.decode()


def test_preview_invoice_format_pdf(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/preview", {"format": "pdf"})

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "Invoice" in response.content.decode()


def test_preview_invoice_requires_authentication(api_client):
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}/preview")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "status_code": 403,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_preview_revision_highlights_correction(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    revision = InvoiceFactory(account=account, previous_revision=invoice, head=invoice.head)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{revision.id}/preview", {"format": "pdf"})

    assert response.status_code == 200
    assert "Corrective Invoice" in response.content.decode()
