import uuid

import pytest

from tests.factories import PriceFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_delete_product(api_client, user, account):
    product_to_delete = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/products/{product_to_delete.id}")

    assert response.status_code == 204


def test_delete_product_rejects_foreign_account(api_client, user, account):
    other_product = ProductFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/products/{other_product.id}")

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


def test_delete_product_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/products/{uuid.uuid4()}")

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


def test_delete_product_requires_authentication(api_client, account):
    product = ProductFactory(account=account)

    response = api_client.delete(f"/api/v1/products/{product.id}")

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


def test_delete_product_with_prices(api_client, user, account):
    product = ProductFactory(account=account)
    PriceFactory(account=account, product=product)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/products/{product.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Product is restricted and cannot be deleted.",
            }
        ],
    }
