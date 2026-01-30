import uuid
from unittest.mock import ANY

import pytest

from openinvoice.invoices.choices import InvoiceDocumentRole, InvoiceStatus
from tests.factories import InvoiceDocumentFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_update_invoice_document(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice, memo="Original memo")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document.id}",
        {
            "memo": "Updated memo",
            "footer": "Updated footer",
            "custom_fields": {"ref": "DOC-UPDATED"},
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(document.id),
        "role": document.role,
        "language": document.language,
        "footer": "Updated footer",
        "memo": "Updated memo",
        "custom_fields": {"ref": "DOC-UPDATED"},
        "file_id": None,
        "created_at": ANY,
        "updated_at": ANY,
    }
    document.refresh_from_db()
    assert document.memo == "Updated memo"
    assert document.footer == "Updated footer"
    assert document.custom_fields == {"ref": "DOC-UPDATED"}


@pytest.mark.parametrize(
    "role",
    [
        InvoiceDocumentRole.SECONDARY,
        InvoiceDocumentRole.LEGAL,
    ],
)
def test_update_invoice_document_rejects_primary_role_change(api_client, user, account, role):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice, role=InvoiceDocumentRole.PRIMARY)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document.id}",
        {"role": role},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "role",
                "code": "invalid",
                "detail": "Invoice must have a primary document",
            }
        ],
    }


def test_update_invoice_document_rejects_invalid_role(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document.id}",
        {"role": "invalid"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "role",
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
def test_update_invoice_document_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    document = InvoiceDocumentFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document.id}",
        {"memo": "Updated memo"},
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


def test_update_invoice_document_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document_id}",
        {"memo": "Updated memo"},
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


def test_update_invoice_document_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()
    document = InvoiceDocumentFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}/documents/{document.id}",
        {"memo": "Updated memo"},
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


def test_update_invoice_document_requires_authentication(api_client):
    invoice_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = api_client.put(
        f"/api/v1/invoices/{invoice_id}/documents/{document_id}",
        {"memo": "Updated memo"},
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


def test_update_invoice_document_requires_account(api_client, user):
    invoice_id = uuid.uuid4()
    document_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/invoices/{invoice_id}/documents/{document_id}",
        {"memo": "Updated memo"},
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
