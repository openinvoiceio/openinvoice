import uuid

import pytest

from openinvoice.quotes.choices import QuoteStatus
from tests.factories import CustomerFactory, PriceFactory, QuoteFactory, QuoteLineFactory

pytestmark = pytest.mark.django_db


def test_update_quote_line(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    line = QuoteLineFactory(quote=quote, quantity=1, description="Premium", unit_amount="50.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Premium plan",
            "quantity": 3,
            "unit_amount": "75.25",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "description": "Premium plan",
        "quantity": 3,
        "unit_amount": "75.25",
        "price_id": None,
        "product_id": None,
        "amount": "225.75",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "225.75",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "225.75",
        "discounts": [],
        "taxes": [],
    }


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_update_quote_line_requires_draft_status(api_client, user, account, status):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer, status=status, number="QT-200")
    line = QuoteLineFactory(quote=quote, quantity=1, description="Standard", unit_amount="30.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Standard plan",
            "quantity": 2,
            "unit_amount": "45.00",
        },
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


def test_update_quote_line_not_found(api_client, user, account):
    line_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quote-lines/{line_id}",
        {
            "description": "Updated description",
            "quantity": 2,
            "unit_amount": "60.00",
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


def test_update_quote_line_invalid_price(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, quantity=1, description="Basic", unit_amount="20.00")
    price_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Basic plan",
            "quantity": 2,
            "price_id": str(price_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "price_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{price_id}" - object does not exist.',
            }
        ],
    }


def test_update_quote_line_price_currency_mismatch(api_client, user, account):
    quote = QuoteFactory(account=account, currency="EUR")
    line = QuoteLineFactory(quote=quote, quantity=1, description="Basic", unit_amount="20.00")
    price = PriceFactory(account=account, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Basic plan",
            "quantity": 2,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Price currency does not match quote currency",
            }
        ],
    }


# TODO: add tests for unit_amount and price validations


def test_update_quote_line_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, quantity=1, description="Basic", unit_amount="20.00")

    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Basic plan",
            "quantity": 2,
            "unit_amount": "25.00",
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


def test_update_quote_line_requires_account(api_client, user):
    quote = QuoteFactory()
    line = QuoteLineFactory(quote=quote, quantity=1, description="Basic", unit_amount="20.00")

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/quote-lines/{line.id}",
        {
            "description": "Basic plan",
            "quantity": 2,
            "unit_amount": "25.00",
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
