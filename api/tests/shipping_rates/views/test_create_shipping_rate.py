from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from common.choices import LimitCode

pytestmark = pytest.mark.django_db


def test_create_shipping_rate(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/shipping-rates",
        data={
            "name": "Standard Shipping",
            "code": "STD",
            "currency": "USD",
            "amount": "5.00",
            "tax_policy": "match_goods",
            "metadata": {"key": "value"},
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "name": "Standard Shipping",
        "code": "STD",
        "currency": "USD",
        "amount": "5.00",
        "tax_policy": "match_goods",
        "is_active": True,
        "metadata": {"key": "value"},
        "archived_at": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_shipping_rate_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/shipping-rates",
        data={
            "name": "Standard Shipping",
            "code": "STD",
            "currency": "USD",
            "amount": "5.00",
            "tax_policy": "match_goods",
            "metadata": {"key": "value"},
        },
    )

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


def test_create_shipping_rate_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/shipping-rates",
        data={
            "name": "Standard Shipping",
            "code": "STD",
            "currency": "USD",
            "amount": "5.00",
            "tax_policy": "match_goods",
            "metadata": {"key": "value"},
        },
    )

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


def test_create_shipping_rate_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_SHIPPING_RATES: 0}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/shipping-rates",
        data={"name": "Standard Shipping"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }
