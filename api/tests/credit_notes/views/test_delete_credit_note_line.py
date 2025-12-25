import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from apps.credit_notes.enums import CreditNoteStatus
from apps.credit_notes.models import CreditNoteLine
from tests.factories import CreditNoteFactory, CreditNoteLineFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_delete_credit_note_line(api_client, user, account):
    credit_note = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    line = CreditNoteLineFactory(credit_note=credit_note)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}")

    assert response.status_code == 204
    assert not CreditNoteLine.objects.filter(id=line.id).exists()


def test_delete_credit_note_line_requires_authentication(api_client, account):
    line = CreditNoteLineFactory(credit_note=CreditNoteFactory(invoice=InvoiceFactory(account=account)))

    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_delete_credit_note_line_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.delete(f"/api/v1/credit-note-lines/{uuid.uuid4()}")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }


def test_delete_credit_note_line_rejects_foreign_account(api_client, user, account):
    line = CreditNoteLineFactory()

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}")

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


@pytest.mark.parametrize("status", [CreditNoteStatus.ISSUED, CreditNoteStatus.VOIDED])
def test_delete_credit_note_line_cannot_modify_finalized(api_client, user, account, status):
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=status,
        number="CN-40",
    )
    line = CreditNoteLineFactory(credit_note=credit_note)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/credit-note-lines/{line.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot modify issued credit note",
            }
        ],
    }
