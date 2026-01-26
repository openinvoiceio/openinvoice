import uuid

import pytest

from apps.quotes.choices import QuoteStatus
from apps.quotes.models import Quote
from tests.factories import QuoteFactory

pytestmark = pytest.mark.django_db


def test_delete_quote(api_client, user, account):
    quote = QuoteFactory(account=account, number="QT-100", status=QuoteStatus.DRAFT)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}")

    assert response.status_code == 204
    assert Quote.objects.filter(id=quote.id).exists() is False


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_delete_quote_requires_draft_status(api_client, user, account, status):
    quote = QuoteFactory(account=account, status=status, number="QT-101")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be deleted",
            }
        ],
    }


def test_delete_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote_id}")

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


def test_delete_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/quotes/{quote_id}")

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


def test_delete_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.delete(f"/api/v1/quotes/{quote_id}")

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
