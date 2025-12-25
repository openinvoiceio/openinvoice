import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from tests.factories import PriceFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_update_product(api_client, user, account):
    existing_product = ProductFactory(account=account, name="Old", description="Old")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{existing_product.id}",
        data={
            "name": "New",
            "description": None,
            "url": None,
            "image_id": None,
            "default_price_id": None,
            "metadata": {},
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(existing_product.id),
        "account_id": str(account.id),
        "name": "New",
        "description": None,
        "is_active": True,
        "url": None,
        "image_url": None,
        "image_id": None,
        "default_price": None,
        "prices_count": 0,
        "metadata": {},
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_product_image_not_found(api_client, user, account):
    product = ProductFactory(account=account)
    image_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{product.id}",
        data={
            "name": "New",
            "description": product.description,
            "url": product.url,
            "image_id": str(image_id),
            "default_price_id": None,
            "metadata": product.metadata,
        },
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


def test_update_product_default_price(api_client, user, account):
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, product=product)
    assert product.default_price is None

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{product.id}",
        data={
            "default_price_id": str(price.id),
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(product.id),
        "account_id": str(account.id),
        "name": product.name,
        "description": product.description,
        "is_active": True,
        "url": None,
        "image_url": None,
        "image_id": None,
        "default_price": {
            "id": str(price.id),
            "currency": price.currency,
            "amount": f"{price.amount.amount:.2f}",
            "metadata": price.metadata,
            "code": price.code,
            "model": price.model,
            "tiers": [],
        },
        "prices_count": 1,
        "metadata": {},
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_product_rejects_foreign_default_price(api_client, user, account):
    product = ProductFactory(account=account)
    foreign_price = PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{product.id}",
        data={
            "default_price_id": str(foreign_price.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "default_price_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{foreign_price.id}" - object does not exist.',
            }
        ],
    }


def test_update_product_default_price_not_found(api_client, user, account):
    product = ProductFactory(account=account)
    price_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{product.id}",
        data={
            "name": "New",
            "description": product.description,
            "url": product.url,
            "image_id": product.image_id,
            "default_price_id": str(price_id),
            "metadata": product.metadata,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "default_price_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{price_id}" - object does not exist.',
            }
        ],
    }


def test_update_product_rejects_foreign_account(api_client, user, account):
    other_product = ProductFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{other_product.id}",
        data={"name": "New"},
    )

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_update_product_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(f"/api/v1/products/{uuid.uuid4()}", data={"name": "New"})

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


def test_update_product_requires_authentication(api_client, account):
    product = ProductFactory(account=account)

    response = api_client.put(f"/api/v1/products/{product.id}", data={"name": "New"})

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


def test_update_product_archived(api_client, user, account):
    product = ProductFactory(account=account, is_active=False, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/products/{product.id}",
        data={"name": "New"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Archived products cannot be updated",
            }
        ],
    }
