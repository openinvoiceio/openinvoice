import uuid

import pytest

from openinvoice.invoices.choices import InvoiceDocumentRole, InvoiceStatus
from openinvoice.invoices.models import InvoiceDocument
from tests.factories import InvoiceDocumentFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_document(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.PRIMARY)
    document = InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.SECONDARY)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document.id}")

    assert response.status_code == 204
    assert not InvoiceDocument.objects.filter(id=document.id).exists()


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_delete_invoice_document_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    document = InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.SECONDARY)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document.id}")

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


def test_delete_invoice_document_rejects_primary_document(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.PRIMARY)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Primary document cannot be deleted",
            }
        ],
    }


def test_delete_invoice_document_rejects_last_document(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.SECONDARY)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Invoice must have at least one document",
            }
        ],
    }


def test_delete_invoice_document_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document_id}")

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


def test_delete_invoice_document_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()
    document = InvoiceDocumentFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/documents/{document.id}")

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


def test_delete_invoice_document_requires_authentication(api_client):
    invoice_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = api_client.delete(f"/api/v1/invoices/{invoice_id}/documents/{document_id}")

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


def test_delete_invoice_document_requires_account(api_client, user):
    invoice_id = uuid.uuid4()
    document_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoices/{invoice_id}/documents/{document_id}")

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
