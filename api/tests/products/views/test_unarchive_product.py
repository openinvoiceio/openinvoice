import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_unarchive_product(api_client, user, account):
    product = ProductFactory(account=account, is_active=False, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{product.id}/unarchive")

    assert response.status_code == 200
    assert response.data == {
        "id": str(product.id),
        "account_id": str(account.id),
        "name": "Test Product",
        "description": "Test product",
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


def test_unarchive_product_already_active(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{product.id}/unarchive")

    assert response.status_code == 200
    assert response.data["is_active"] is True


def test_unarchive_product_rejects_foreign_account(api_client, user, account):
    other_product = ProductFactory(is_active=False, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{other_product.id}/unarchive")

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


def test_unarchive_product_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/products/{uuid.uuid4()}/unarchive")

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


def test_unarchive_product_requires_authentication(api_client, account):
    product = ProductFactory(account=account, is_active=False, archived_at=timezone.now())

    response = api_client.post(f"/api/v1/products/{product.id}/unarchive")

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
