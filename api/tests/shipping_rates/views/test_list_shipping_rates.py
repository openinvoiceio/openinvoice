from unittest.mock import ANY

import pytest

from tests.factories import ShippingRateFactory

pytestmark = pytest.mark.django_db


def test_list_shipping_rates(api_client, user, account):
    first_rate = ShippingRateFactory(account=account)
    second_rate = ShippingRateFactory(account=account)
    ShippingRateFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/shipping-rates")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(rate.id),
                "account_id": str(account.id),
                "name": rate.name,
                "code": rate.code,
                "currency": rate.currency,
                "amount": str(rate.amount.amount),
                "tax_policy": rate.tax_policy,
                "status": rate.status,
                "metadata": rate.metadata,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
            }
            for rate in [second_rate, first_rate]
        ],
    }


def test_list_shipping_rates_rejects_foreign_account(api_client, user, account):
    owned_rate = ShippingRateFactory(account=account)
    ShippingRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/shipping-rates")

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(owned_rate.id)]


def test_list_shipping_rates_requires_authentication(api_client):
    response = api_client.get("/api/v1/shipping-rates")

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


def test_list_shipping_rates_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/shipping-rates")

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
