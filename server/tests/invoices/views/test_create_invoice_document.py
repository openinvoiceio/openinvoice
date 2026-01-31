import uuid
from unittest.mock import ANY

import pytest

from openinvoice.invoices.choices import InvoiceDocumentAudience, InvoiceStatus
from openinvoice.invoices.models import InvoiceDocument
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_create_invoice_document(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/documents",
        {
            "language": "en-us",
            "footer": "Footer",
            "memo": "Memo",
            "custom_fields": {"ref": "DOC-1"},
        },
    )

    assert response.status_code == 201
    document = InvoiceDocument.objects.get(id=response.data["id"])
    assert response.data == {
        "id": str(document.id),
        "audience": [InvoiceDocumentAudience.INTERNAL],
        "language": "en-us",
        "footer": "Footer",
        "memo": "Memo",
        "custom_fields": {"ref": "DOC-1"},
        "file_id": None,
        "created_at": ANY,
        "updated_at": ANY,
    }
    assert document.invoice_id == invoice.id


def test_create_invoice_document_rejects_invalid_language(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/documents",
        {
            "language": "invalid",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "language",
                "code": "invalid_choice",
                "detail": '"invalid" is not a valid choice.',
            }
        ],
    }


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_create_invoice_document_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/documents",
        {
            "language": "en-us",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be modified",
            }
        ],
    }


def test_create_invoice_document_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice_id}/documents",
        {"language": "en-us"},
    )

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


def test_create_invoice_document_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/documents",
        {"language": "en-us"},
    )

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


def test_create_invoice_document_requires_authentication(api_client):
    invoice_id = uuid.uuid4()

    response = api_client.post(
        f"/api/v1/invoices/{invoice_id}/documents",
        {"language": "en-us"},
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


def test_create_invoice_document_requires_account(api_client, user):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/invoices/{invoice_id}/documents",
        {"language": "en-us"},
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
