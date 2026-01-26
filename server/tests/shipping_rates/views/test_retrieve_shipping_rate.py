import uuid
from unittest.mock import ANY

import pytest

from tests.factories import ShippingRateFactory

pytestmark = pytest.mark.django_db


def test_retrieve_shipping_rate(api_client, user, account):
    shipping_rate = ShippingRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-rates/{shipping_rate.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(shipping_rate.id),
        "account_id": str(account.id),
        "name": shipping_rate.name,
        "code": shipping_rate.code,
        "currency": shipping_rate.currency,
        "amount": str(shipping_rate.amount.amount),
        "status": shipping_rate.status,
        "metadata": shipping_rate.metadata,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
    }


def test_retrieve_shipping_rate_not_found(api_client, user, account):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-rates/{shipping_rate_id}")

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


def test_retrieve_shipping_rate_rejects_foreign_account(api_client, user, account):
    other_rate = ShippingRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-rates/{other_rate.id}")

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


def test_retrieve_shipping_rate_requires_authentication(api_client):
    shipping_rate_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/shipping-rates/{shipping_rate_id}")

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


def test_retrieve_shipping_rate_requires_account(api_client, user):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/shipping-rates/{shipping_rate_id}")

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
