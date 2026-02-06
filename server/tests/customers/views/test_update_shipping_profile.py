import uuid
from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory, ShippingProfileFactory

pytestmark = pytest.mark.django_db


def test_update_shipping_profile(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_profile = ShippingProfileFactory(name="Old")
    customer.shipping_profiles.add(shipping_profile)
    line2 = shipping_profile.address.line2
    state = shipping_profile.address.state

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-profiles/{shipping_profile.id}",
        {
            "name": "New",
            "phone": "555",
            "address": {
                "line1": "New Line",
                "locality": "City",
                "postal_code": "123",
                "country": "US",
            },
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(shipping_profile.id),
        "name": "New",
        "phone": "555",
        "address": {
            "line1": "New Line",
            "line2": line2,
            "locality": "City",
            "state": state,
            "postal_code": "123",
            "country": "US",
        },
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_shipping_profile_requires_authentication(api_client):
    response = api_client.put(
        f"/api/v1/shipping-profiles/{uuid.uuid4()}",
        {"name": "New"},
    )

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


def test_update_shipping_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/shipping-profiles/{uuid.uuid4()}",
        {"name": "New"},
    )

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


def test_update_shipping_profile_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()
    shipping_profile = ShippingProfileFactory()
    customer.shipping_profiles.add(shipping_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/shipping-profiles/{shipping_profile.id}",
        {"name": "New"},
    )

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
