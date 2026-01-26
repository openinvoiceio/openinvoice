import uuid

import pytest

from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db

# TODO: add more asserts of rendered html


def test_preview_quote_returns_pdf_template(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote.id}/preview")

    assert response.status_code == 200
    assert response.template_name == "quotes/pdf/classic.html"


def test_preview_quote_email_template(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote.id}/preview", {"format": "email"})

    assert response.status_code == 200
    assert response.template_name == "quotes/email/quote_email_message.html"


def test_preview_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote_id}/preview")

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


def test_preview_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/quotes/{quote_id}/preview")

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


def test_preview_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/quotes/{quote_id}/preview")

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
