import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from openinvoice.comments.choices import CommentVisibility
from tests.factories import CommentFactory, QuoteFactory

pytestmark = pytest.mark.django_db


def test_list_quote_comments(api_client, user, account):
    quote = QuoteFactory(account=account)
    base_time = timezone.now().replace(microsecond=0)
    first_comment = CommentFactory(
        author=user,
        content="First comment",
        visibility=CommentVisibility.PUBLIC,
        created_at=base_time - timedelta(hours=2),
    )
    second_comment = CommentFactory(
        author=user,
        content="Second comment",
        visibility=CommentVisibility.INTERNAL,
        created_at=base_time - timedelta(hours=1),
    )
    quote.comments.add(first_comment, second_comment)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote.id}/comments")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(first_comment.id),
                "content": "First comment",
                "visibility": CommentVisibility.PUBLIC,
                "created_at": first_comment.created_at.isoformat().replace("+00:00", "Z"),
                "author": {
                    "id": user.id,
                    "name": user.name,
                    "avatar_url": None,
                },
            },
            {
                "id": str(second_comment.id),
                "content": "Second comment",
                "visibility": CommentVisibility.INTERNAL,
                "created_at": second_comment.created_at.isoformat().replace("+00:00", "Z"),
                "author": {
                    "id": user.id,
                    "name": user.name,
                    "avatar_url": None,
                },
            },
        ],
    }


def test_list_quote_comments_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote_id}/comments")

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


def test_list_quote_comments_rejects_foreign_account(api_client, user, account):
    quote = QuoteFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote.id}/comments")

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


def test_list_quote_comments_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/quotes/{quote_id}/comments")

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


def test_list_quote_comments_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/quotes/{quote_id}/comments")

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
