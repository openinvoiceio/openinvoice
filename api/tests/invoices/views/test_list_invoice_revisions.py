import uuid

import pytest

from apps.invoices.enums import InvoiceStatus
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_list_invoice_revisions(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    revision_1 = InvoiceFactory(
        account=account, status=InvoiceStatus.VOIDED, previous_revision=invoice, head=invoice.head
    )
    revision_2 = InvoiceFactory(
        account=account, status=InvoiceStatus.DRAFT, previous_revision=revision_1, head=invoice.head
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 200
    assert [r["id"] for r in response.data] == [
        str(revision_2.id),
        str(revision_1.id),
        str(invoice.id),
    ]


def test_list_invoice_revisions_no_revisions(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.DRAFT)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 200
    assert [r["id"] for r in response.data] == [str(invoice.id)]


def test_list_invoice_revisions_middle_revision(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    revision_1 = InvoiceFactory(
        account=account, status=InvoiceStatus.VOIDED, previous_revision=invoice, head=invoice.head
    )
    revision_2 = InvoiceFactory(
        account=account, status=InvoiceStatus.DRAFT, previous_revision=revision_1, head=invoice.head
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{revision_1.id}/revisions")

    assert response.status_code == 200
    assert [r["id"] for r in response.data] == [
        str(revision_2.id),
        str(revision_1.id),
        str(invoice.id),
    ]


def test_list_invoice_revisions_different_heads(api_client, user, account):
    invoice_1 = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    InvoiceFactory(account=account, status=InvoiceStatus.VOIDED, previous_revision=invoice_1, head=invoice_1.head)
    invoice_2 = InvoiceFactory(account=account, status=InvoiceStatus.DRAFT)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice_2.id}/revisions")

    assert response.status_code == 200
    assert [r["id"] for r in response.data] == [str(invoice_2.id)]


def test_list_invoice_revisions_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_list_invoice_revisions_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()  # Other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}/revisions")

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


def test_list_invoice_revisions_requires_authentication(api_client):
    invoice_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_list_invoice_revisions_requires_account(api_client, user):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invoices/{invoice_id}/revisions")

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
