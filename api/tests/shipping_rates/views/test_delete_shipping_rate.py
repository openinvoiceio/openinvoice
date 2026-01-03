import uuid

import pytest

from tests.factories import ShippingRateFactory

pytestmark = pytest.mark.django_db


def test_delete_shipping_rate(api_client, user, account):
    shipping_rate = ShippingRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/shipping-rates/{shipping_rate.id}")

    assert response.status_code == 204


def test_delete_shipping_rate_not_found(api_client, user, account):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/shipping-rates/{shipping_rate_id}")

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


def test_delete_shipping_rate_rejects_foreign_account(api_client, user, account):
    other_shipping_rate = ShippingRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/shipping-rates/{other_shipping_rate.id}")

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


def test_delete_shipping_rate_requires_authentication(api_client):
    shipping_rate_id = uuid.uuid4()

    response = api_client.delete(f"/api/v1/shipping-rates/{shipping_rate_id}")

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


def test_delete_shipping_rate_requires_account(api_client, user):
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/shipping-rates/{shipping_rate_id}")

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
