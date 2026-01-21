import uuid
from unittest.mock import ANY

import pytest
from djmoney.money import Money

from apps.prices.choices import PriceModel
from apps.quotes.choices import QuoteStatus
from tests.factories import CustomerFactory, PriceFactory, QuoteFactory

pytestmark = pytest.mark.django_db


def test_create_quote_line_from_unit_amount(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 2,
            "unit_amount": "125.50",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "description": "Enterprise plan",
        "quantity": 2,
        "unit_amount": "125.50",
        "price_id": None,
        "product_id": None,
        "amount": "251.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "251.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "251.00",
        "discounts": [],
        "taxes": [],
    }


def test_create_quote_line_from_flat_price(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    price = PriceFactory(account=account, currency=quote.currency, amount="100.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 3,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "description": "Enterprise plan",
        "quantity": 3,
        "unit_amount": "100.00",
        "price_id": str(price.id),
        "product_id": str(price.product_id),
        "amount": "300.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "300.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "300.00",
        "discounts": [],
        "taxes": [],
    }


def test_create_quote_line_from_volume_price(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    price = PriceFactory(account=account, currency=quote.currency, model=PriceModel.VOLUME)
    price.add_tier(unit_amount=Money("10", price.currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", price.currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 15,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "description": "Enterprise plan",
        "quantity": 15,
        "unit_amount": "8.00",
        "price_id": str(price.id),
        "product_id": str(price.product_id),
        "amount": "120.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "120.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "120.00",
        "discounts": [],
        "taxes": [],
    }


def test_create_quote_line_from_graduated_price(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    price = PriceFactory(account=account, currency=quote.currency, model=PriceModel.GRADUATED)
    price.add_tier(unit_amount=Money("10", price.currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", price.currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 15,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "description": "Enterprise plan",
        "quantity": 15,
        "unit_amount": "9.47",
        "price_id": str(price.id),
        "product_id": str(price.product_id),
        "amount": "142.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "142.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "142.00",
        "discounts": [],
        "taxes": [],
    }


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_create_quote_line_requires_draft_status(api_client, user, account, status):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer, status=status, number="QT-100")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 2,
            "unit_amount": "125.50",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Only draft quotes can be modified",
            }
        ],
    }


def test_create_quote_line_invalid_quote(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote_id),
            "description": "Enterprise plan",
            "quantity": 2,
            "unit_amount": "125.50",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "quote_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{quote_id}" - object does not exist.',
            }
        ],
    }


def test_create_quote_line_invalid_price_and_unit_amount(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    price_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
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


def test_create_quote_line_price_currency_mismatch(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer, currency="USD")
    price = PriceFactory(account=account, currency="EUR", amount="100.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
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


def test_create_quote_line_without_price_or_unit_amount(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 2,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Exactly one of the fields unit_amount, price_id must be provided.",
            }
        ],
    }


def test_create_quote_line_with_price_and_unit_amount(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    price = PriceFactory(account=account, currency=quote.currency, amount="100.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote.id),
            "description": "Enterprise plan",
            "quantity": 2,
            "price_id": str(price.id),
            "unit_amount": "150.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Exactly one of the fields unit_amount, price_id must be provided.",
            }
        ],
    }


def test_create_quote_line_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote_id),
            "description": "Enterprise plan",
            "quantity": 2,
            "unit_amount": "125.50",
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


def test_create_quote_line_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/quote-lines",
        {
            "quote_id": str(quote_id),
            "description": "Enterprise plan",
            "quantity": 2,
            "unit_amount": "125.50",
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
