import uuid

import pytest

from openinvoice.quotes.choices import QuoteStatus
from openinvoice.quotes.models import Quote, QuoteLine
from tests.factories import QuoteFactory, QuoteLineFactory

pytestmark = pytest.mark.django_db


def test_delete_quote_line(api_client, user, account):
    quote = QuoteFactory(account=account, status=QuoteStatus.DRAFT)
    line = QuoteLineFactory(quote=quote)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}")

    assert response.status_code == 204
    assert QuoteLine.objects.filter(id=line.id).exists() is False
    assert Quote.objects.filter(id=quote.id).exists() is True
    # TODO: assert quote recalculated? Maybe as separate test


def test_delete_quote_line_not_found(api_client, user, account):
    line_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line_id}")

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


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_delete_quote_line_requires_draft_quote_status(api_client, user, account, status):
    quote = QuoteFactory(account=account, status=status, number="QT-202")
    line = QuoteLineFactory(quote=quote)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be modified",
            }
        ],
    }


def test_delete_quote_line_requires_account(api_client, user):
    line_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/quote-lines/{line_id}")

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


def test_delete_quote_line_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account, status=QuoteStatus.DRAFT)
    line = QuoteLineFactory(quote=quote)

    response = api_client.delete(f"/api/v1/quote-lines/{line.id}")

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
