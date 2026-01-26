import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone

from openinvoice.products.choices import ProductStatus
from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_archive_product(api_client, user, account):
    product = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{product.id}/archive")

    assert response.status_code == 200
    assert response.data == {
        "id": str(product.id),
        "account_id": str(account.id),
        "name": "Test Product",
        "description": "Test product",
        "status": "archived",
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


def test_archive_product_already_archived(api_client, user, account):
    product = ProductFactory(account=account, status=ProductStatus.ARCHIVED, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{product.id}/archive")

    assert response.status_code == 200
    assert response.data["status"] == "archived"


def test_archive_product_rejects_foreign_account(api_client, user, account):
    other_product = ProductFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/products/{other_product.id}/archive")

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


def test_archive_product_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/products/{uuid.uuid4()}/archive")

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


def test_archive_product_requires_authentication(api_client, account):
    product = ProductFactory(account=account)

    response = api_client.post(f"/api/v1/products/{product.id}/archive")

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
