import uuid

import pytest

from tests.factories import InvoiceFactory, InvoiceLineFactory, PriceFactory

pytestmark = pytest.mark.django_db


def test_delete_price(api_client, user, account):
    price_to_delete = PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/prices/{price_to_delete.id}")

    assert response.status_code == 204


def test_delete_price_rejects_foreign_account(api_client, user, account):
    other_price = PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/prices/{other_price.id}")

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


def test_delete_price_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/prices/{uuid.uuid4()}")

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


def test_delete_price_in_use(api_client, user, account):
    price = PriceFactory(account=account)
    invoice = InvoiceFactory(account=account, currency=price.currency)
    InvoiceLineFactory(invoice=invoice, price=price, currency=price.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/prices/{price.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "This object cannot be deleted because it has related data.",
            }
        ],
    }


def test_delete_price_default(api_client, user, account):
    price = PriceFactory(account=account)
    price.product.default_price_id = price.id
    price.product.save()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/prices/{price.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "This object cannot be deleted because it has related data.",
            }
        ],
    }


def test_delete_price_requires_authentication(api_client, account):
    price = PriceFactory(account=account)

    response = api_client.delete(f"/api/v1/prices/{price.id}")

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
