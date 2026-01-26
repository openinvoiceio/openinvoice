import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from openinvoice.quotes.choices import QuoteStatus
from tests.factories import QuoteFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_add_quote_tax(api_client, user, account):
    quote = QuoteFactory(account=account)
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("2.50"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "tax_rate_id": str(tax_rate.id),
        "name": tax_rate.name,
        "description": tax_rate.description,
        "rate": "2.50",
        "amount": "0.00",
    }


def test_add_quote_tax_not_found(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote_id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_add_quote_tax_requires_draft_status(api_client, user, account, status):
    quote = QuoteFactory(account=account, status=status, number="QT-100")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

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


def test_add_quote_tax_invalid_tax_rate(api_client, user, account):
    quote = QuoteFactory(account=account)
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id}" - object does not exist.',
            }
        ],
    }


def test_add_quote_tax_tax_rate_already_applied(api_client, user, account):
    quote = QuoteFactory(account=account)
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    quote.add_tax(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "invalid",
                "detail": "Given tax rate is already applied to this quote",
            }
        ],
    }


def test_add_quote_tax_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("15.00"))

    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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


def test_add_quote_tax_requires_account(api_client, user):
    quote = QuoteFactory()
    tax_rate = TaxRateFactory()

    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/quotes/{quote.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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
