import uuid

import pytest

from tests.factories import CreditNoteFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_preview_credit_note(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}/preview")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "Credit Note" in response.content.decode()


def test_preview_credit_note_email_format(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        f"/api/v1/credit-notes/{credit_note.id}/preview",
        {"format": "email"},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "credit-note" in response.content.decode()


def test_preview_credit_note_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}/preview")

    assert response.status_code == 404
    assert response.data == {
        "type": "client_error",
        "status_code": 404,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_preview_credit_note_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/credit-notes/{uuid.uuid4()}/preview")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "status_code": 403,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }


def test_preview_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account), number="CN-1")

    response = api_client.get(f"/api/v1/credit-notes/{credit_note.id}/preview")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "status_code": 403,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }
