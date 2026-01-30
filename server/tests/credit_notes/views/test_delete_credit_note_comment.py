import uuid

import pytest

from openinvoice.comments.choices import CommentVisibility
from openinvoice.comments.models import Comment
from tests.factories import CommentFactory, CreditNoteFactory

pytestmark = pytest.mark.django_db


def test_delete_credit_note_comment(api_client, user, account):
    credit_note = CreditNoteFactory(account=account)
    comment = CommentFactory(
        author=user,
        content="Delete me",
        visibility=CommentVisibility.INTERNAL,
    )
    credit_note.comments.add(comment)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}/comments/{comment.id}")

    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment.id).exists()


def test_delete_credit_note_comment_not_found(api_client, user, account):
    credit_note = CreditNoteFactory(account=account)
    comment_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}/comments/{comment_id}")

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


def test_delete_credit_note_comment_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()
    comment = CommentFactory(
        author=user,
        content="Foreign",
        visibility=CommentVisibility.PUBLIC,
    )
    credit_note.comments.add(comment)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}/comments/{comment.id}")

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


def test_delete_credit_note_comment_requires_authentication(api_client, account):
    credit_note = CreditNoteFactory(account=account)
    comment = CommentFactory(
        author=credit_note.account.created_by,
        content="Auth",
        visibility=CommentVisibility.PUBLIC,
    )
    credit_note.comments.add(comment)

    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}/comments/{comment.id}")

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


def test_delete_credit_note_comment_requires_account(api_client, user):
    credit_note = CreditNoteFactory()
    comment = CommentFactory(
        author=user,
        content="Account",
        visibility=CommentVisibility.INTERNAL,
    )
    credit_note.comments.add(comment)

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/credit-notes/{credit_note.id}/comments/{comment.id}")

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
