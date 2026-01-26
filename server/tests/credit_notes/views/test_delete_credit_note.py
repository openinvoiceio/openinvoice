import uuid

import pytest

from openinvoice.credit_notes.choices import CreditNoteStatus
from openinvoice.credit_notes.models import CreditNote
from tests.factories import CreditNoteFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_delete_credit_note(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}")

    assert response.status_code == 204
    assert not CreditNote.objects.filter(id=credit_note.id).exists()


def test_delete_credit_note_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}")

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


def test_delete_credit_note_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.delete(f"/api/v1/credit-notes/{uuid.uuid4()}")

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


def test_delete_credit_note_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}")

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


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_delete_credit_note_not_allowed_when_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-30",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft credit notes can be deleted",
            }
        ],
    }
