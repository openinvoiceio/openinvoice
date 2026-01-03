import uuid
from unittest.mock import ANY

import pytest

from tests.factories import ShippingRateFactory

pytestmark = pytest.mark.django_db


def test_update_shipping_rate(api_client, user, account):
    shipping_rate = ShippingRateFactory(
        account=account,
        name="Standard Shipping",
        code="STD",
        currency="USD",
        amount="10.00",
        tax_policy="match_goods",
        metadata={"key": "value"},
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate.id}",
        data={
            "name": "Express Shipping",
            "code": "EXP",
            "currency": "USD",
            "amount": "15.00",
            "tax_policy": "exempt",
            "metadata": {"updated_key": "updated_value"},
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(shipping_rate.id),
        "account_id": str(account.id),
        "name": "Express Shipping",
        "code": "EXP",
        "currency": "USD",
        "amount": "15.00",
        "tax_policy": "exempt",
        "is_active": True,
        "metadata": {"updated_key": "updated_value"},
        "archived_at": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_shipping_rate_archived(api_client, user, account):
    shipping_rate = ShippingRateFactory(account=account, is_active=False)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate.id}",
        data={"name": "Express Shipping"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Archived shipping rate cannot be updated",
            }
        ],
    }


def test_update_shipping_rate_not_found(api_client, user, account):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate_id}",
        data={"name": "Express Shipping"},
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


def test_update_shipping_rate_requires_authentication(api_client):
    shipping_rate_id = uuid.uuid4()

    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate_id}",
        data={"name": "Express Shipping"},
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


def test_update_shipping_rate_requires_account(api_client, user):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate_id}",
        data={"name": "Express Shipping"},
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


def test_update_shipping_rate_rejects_foreign_account(api_client, user, account):
    shipping_rate = ShippingRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-rates/{shipping_rate.id}",
        data={"name": "Express Shipping"},
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
