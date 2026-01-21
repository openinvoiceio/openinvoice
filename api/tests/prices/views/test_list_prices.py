from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.prices.choices import PriceModel
from tests.factories import PriceFactory

pytestmark = pytest.mark.django_db


def test_list_prices(api_client, user, account):
    first_price = PriceFactory(account=account)
    second_price = PriceFactory(account=account)
    PriceFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(price.id),
                "account_id": str(account.id),
                "product": {
                    "id": str(price.product.id),
                    "name": price.product.name,
                    "description": "Test product",
                    "is_active": True,
                    "default_price_id": None,
                    "metadata": {},
                    "created_at": ANY,
                    "updated_at": ANY,
                },
                "currency": "PLN",
                "amount": "10.00",
                "model": PriceModel.FLAT,
                "is_active": True,
                "metadata": {},
                "is_used": False,
                "code": None,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
                "tiers": [],
            }
            for price in [second_price, first_price]
        ],
    }


def test_list_prices_rejects_foreign_account(api_client, user, account):
    owned_price = PriceFactory(account=account)
    PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(owned_price.id)]


def test_list_prices_requires_authentication(api_client):
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_list_prices_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
