import uuid
from unittest.mock import ANY

import pytest

from openinvoice.comments.choices import CommentVisibility
from openinvoice.comments.models import Comment
from tests.factories import CreditNoteFactory

pytestmark = pytest.mark.django_db


def test_create_credit_note_comment(api_client, user, account):
    credit_note = CreditNoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note.id}/comments",
        data={
            "content": "Credit note comment",
            "visibility": CommentVisibility.PUBLIC,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "content": "Credit note comment",
        "visibility": CommentVisibility.PUBLIC,
        "created_at": ANY,
        "author": {
            "id": user.id,
            "name": user.name,
            "avatar_url": None,
        },
    }
    comment = Comment.objects.get(id=response.data["id"])
    assert comment.author_id == user.id
    assert credit_note.comments.filter(id=comment.id).exists()


def test_create_credit_note_comment_not_found(api_client, user, account):
    credit_note_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note_id}/comments",
        data={
            "content": "Credit note comment",
            "visibility": CommentVisibility.PUBLIC,
        },
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


def test_create_credit_note_comment_rejects_foreign_account(api_client, user, account):
    credit_note = CreditNoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note.id}/comments",
        data={
            "content": "Credit note comment",
            "visibility": CommentVisibility.PUBLIC,
        },
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


def test_create_credit_note_comment_requires_authentication(api_client):
    credit_note_id = uuid.uuid4()

    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note_id}/comments",
        data={
            "content": "Credit note comment",
            "visibility": CommentVisibility.PUBLIC,
        },
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


def test_create_credit_note_comment_requires_account(api_client, user):
    credit_note_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/credit-notes/{credit_note_id}/comments",
        data={
            "content": "Credit note comment",
            "visibility": CommentVisibility.PUBLIC,
        },
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
