import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.prices.choices import PriceModel
from common.choices import LimitCode

pytestmark = pytest.mark.django_db


def test_create_product(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/products",
        data={
            "name": "Product 1",
            "description": None,
            "url": None,
            "image_id": None,
            "metadata": None,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "name": "Product 1",
        "description": None,
        "status": "active",
        "url": None,
        "image_url": None,
        "image_id": None,
        "default_price": None,
        "prices_count": 0,
        "metadata": {},
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": ANY,
    }


def test_create_product_with_default_price(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/products",
        data={
            "name": "Product 1",
            "description": None,
            "url": None,
            "image_id": None,
            "default_price": {
                "currency": "PLN",
                "amount": "10.00",
                "metadata": {"key": "value"},
                "code": "PRICE_CODE",
            },
            "metadata": None,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "name": "Product 1",
        "description": None,
        "status": "active",
        "url": None,
        "image_url": None,
        "image_id": None,
        "default_price": {
            "id": ANY,
            "currency": "PLN",
            "amount": "10.00",
            "model": PriceModel.FLAT,
            "tiers": [],
            "metadata": {"key": "value"},
            "code": "PRICE_CODE",
        },
        "prices_count": 1,
        "metadata": {},
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": ANY,
    }


def test_create_product_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/products",
        data={
            "name": "Product 1",
            "description": None,
            "url": None,
            "image_id": None,
            "metadata": None,
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


def test_create_product_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/products",
        data={
            "name": "Product 1",
            "description": None,
            "url": None,
            "image_id": None,
            "metadata": None,
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


def test_create_product_image_not_found(api_client, user, account):
    image_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/products",
        data={"name": "Product", "image_id": str(image_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "image_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{image_id}" - object does not exist.',
            }
        ],
    }


def test_create_product_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_PRODUCTS: 0}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/products",
        data={"name": "Product 1"},
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
