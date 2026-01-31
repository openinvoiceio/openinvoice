import uuid
from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone

from openinvoice.invoices.choices import InvoiceDocumentAudience
from tests.factories import InvoiceDocumentFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_list_invoice_documents(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    base_time = timezone.now().replace(microsecond=0)
    first_document = InvoiceDocumentFactory(
        invoice=invoice,
        audience=[InvoiceDocumentAudience.CUSTOMER],
        created_at=base_time - timedelta(hours=1),
    )
    second_document = InvoiceDocumentFactory(
        invoice=invoice,
        audience=[InvoiceDocumentAudience.INTERNAL],
        footer="Footer",
        memo="Memo",
        custom_fields={"ref": "DOC-2"},
        created_at=base_time,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/documents")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(first_document.id),
                "audience": first_document.audience,
                "language": first_document.language,
                "footer": first_document.footer,
                "memo": first_document.memo,
                "custom_fields": first_document.custom_fields,
                "file_id": None,
                "created_at": ANY,
                "updated_at": ANY,
            },
            {
                "id": str(second_document.id),
                "audience": second_document.audience,
                "language": second_document.language,
                "footer": second_document.footer,
                "memo": second_document.memo,
                "custom_fields": second_document.custom_fields,
                "file_id": None,
                "created_at": ANY,
                "updated_at": ANY,
            },
        ],
    }


def test_list_invoice_documents_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice_id}/documents")

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


def test_list_invoice_documents_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/documents")

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


def test_list_invoice_documents_requires_authentication(api_client):
    invoice_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/invoices/{invoice_id}/documents")

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


def test_list_invoice_documents_requires_account(api_client, user):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invoices/{invoice_id}/documents")

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
