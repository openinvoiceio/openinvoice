import uuid
from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory, ShippingProfileFactory

pytestmark = pytest.mark.django_db


def test_retrieve_shipping_profile(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_profile = ShippingProfileFactory()
    customer.shipping_profiles.add(shipping_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-profiles/{shipping_profile.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(shipping_profile.id),
        "name": shipping_profile.name,
        "phone": shipping_profile.phone,
        "address": {
            "line1": shipping_profile.address.line1,
            "line2": shipping_profile.address.line2,
            "locality": shipping_profile.address.locality,
            "state": shipping_profile.address.state,
            "postal_code": shipping_profile.address.postal_code,
            "country": str(shipping_profile.address.country),
        },
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_retrieve_shipping_profile_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-profiles/{uuid.uuid4()}")

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


def test_retrieve_shipping_profile_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)
    shipping_profile = ShippingProfileFactory()
    customer.shipping_profiles.add(shipping_profile)

    response = api_client.get(f"/api/v1/shipping-profiles/{shipping_profile.id}")

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


def test_retrieve_shipping_profile_requires_account(api_client, user):
    customer = CustomerFactory()
    shipping_profile = ShippingProfileFactory()
    customer.shipping_profiles.add(shipping_profile)

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/shipping-profiles/{shipping_profile.id}")

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


def test_retrieve_shipping_profile_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()
    shipping_profile = ShippingProfileFactory()
    customer.shipping_profiles.add(shipping_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/shipping-profiles/{shipping_profile.id}")

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
