import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.prices.choices import PriceModel
from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_create_flat_price(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "amount": "10.00",
            "metadata": None,
            "code": None,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "product": {
            "id": str(product.id),
            "name": "Test Product",
            "description": "Test product",
            "status": "active",
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
            "archived_at": ANY,
        },
        "currency": "PLN",
        "amount": "10.00",
        "model": PriceModel.FLAT,
        "status": "active",
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [],
    }


def test_create_volume_price(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "model": PriceModel.VOLUME,
            "tiers": [
                {"unit_amount": "10.00", "from_value": 1, "to_value": 10},
                {"unit_amount": "8.00", "from_value": 11, "to_value": None},
            ],
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "product": {
            "id": str(product.id),
            "name": "Test Product",
            "description": "Test product",
            "status": "active",
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
            "archived_at": ANY,
        },
        "currency": "PLN",
        "amount": "0.00",
        "model": PriceModel.VOLUME,
        "status": "active",
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [
            {"unit_amount": "10.00", "from_value": 1, "to_value": 10},
            {"unit_amount": "8.00", "from_value": 11, "to_value": None},
        ],
    }


def test_create_graduated_price(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "model": PriceModel.GRADUATED,
            "tiers": [
                {"unit_amount": "10.00", "from_value": 0, "to_value": 5},
                {"unit_amount": "8.00", "from_value": 6, "to_value": None},
            ],
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "product": {
            "id": str(product.id),
            "name": "Test Product",
            "description": "Test product",
            "status": "active",
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
            "archived_at": ANY,
        },
        "currency": "PLN",
        "amount": "0.00",
        "model": PriceModel.GRADUATED,
        "status": "active",
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [
            {"unit_amount": "10.00", "from_value": 0, "to_value": 5},
            {"unit_amount": "8.00", "from_value": 6, "to_value": None},
        ],
    }


def test_create_tiered_price_without_tiers(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "model": PriceModel.GRADUATED,
        },
    )

    assert response.status_code == 201
    assert response.data["amount"] == "0.00"
    assert response.data["tiers"] == []


def test_create_price_rejects_non_contiguous_tiers(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "model": PriceModel.VOLUME,
            "tiers": [
                {"unit_amount": "10.00", "from_value": 1, "to_value": 5},
                {"unit_amount": "8.00", "from_value": 7, "to_value": None},
            ],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tiers",
                "code": "invalid",
                "detail": "Tiers must be continuous without gaps",
            }
        ],
    }


def test_create_price_invalid_tiers_range(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "model": PriceModel.VOLUME,
            "tiers": [
                {"unit_amount": "10.00", "from_value": 10, "to_value": 5},
            ],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tiers.0.to_value",
                "code": "invalid",
                "detail": "Upper bound must be greater than or equal to lower bound.",
            }
        ],
    }


def test_create_price_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(uuid.uuid4()),
            "currency": "PLN",
            "amount": "10.00",
            "metadata": None,
            "code": None,
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


def test_create_price_requires_authentication(api_client, account):
    product = ProductFactory(account=account)

    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product.id),
            "currency": "PLN",
            "amount": "10.00",
            "metadata": None,
            "code": None,
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


def test_create_price_product_not_found(api_client, user, account):
    product_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(product_id),
            "currency": "PLN",
            "amount": "10.00",
            "metadata": None,
            "code": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "product_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{product_id}" - object does not exist.',
            }
        ],
    }


def test_create_price_rejects_foreign_account(api_client, user, account):
    other_product = ProductFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/prices",
        data={
            "product_id": str(other_product.id),
            "currency": "PLN",
            "amount": "10.00",
            "metadata": None,
            "code": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "product_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{other_product.id}" - object does not exist.',
            }
        ],
    }
