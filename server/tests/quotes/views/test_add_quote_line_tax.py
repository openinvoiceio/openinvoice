import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from openinvoice.quotes.choices import QuoteStatus
from tests.factories import (
    QuoteFactory,
    QuoteLineFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_add_quote_line_tax(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="150.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("23.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "tax_rate_id": str(tax_rate.id),
        "name": tax_rate.name,
        "description": tax_rate.description,
        "rate": "23.00",
        "amount": "34.50",
    }


def test_add_quote_line_tax_not_found(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    line_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/taxes",
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


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.ACCEPTED, QuoteStatus.CANCELED])
def test_add_quote_line_tax_requires_draft(api_client, user, account, status):
    quote = QuoteFactory(account=account, number="QT-0002", status=status)
    line = QuoteLineFactory(quote=quote, unit_amount="150.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("23.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/taxes",
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


def test_add_quote_line_tax_invalid_tax_rate(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="150.00")
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/taxes",
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


def test_add_quote_line_tax_tax_rate_already_applied(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="150.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("23.00"))
    line.add_tax(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "invalid",
                "detail": "Given tax rate is already applied to this quote line",
            }
        ],
    }


def test_add_quote_line_tax_requires_authentication(api_client):
    line_id = uuid.uuid4()
    tax_rate = TaxRateFactory()

    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/taxes",
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


def test_add_quote_line_tax_requires_account(api_client, user):
    line_id = uuid.uuid4()
    tax_rate = TaxRateFactory()

    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/taxes",
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
