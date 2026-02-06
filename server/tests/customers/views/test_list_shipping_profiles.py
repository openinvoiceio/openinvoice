from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory, ShippingProfileFactory

pytestmark = pytest.mark.django_db


def test_list_shipping_profiles(api_client, user, account):
    customer_1 = CustomerFactory(account=account)
    customer_2 = CustomerFactory(account=account)
    shipping_profile_1 = ShippingProfileFactory(name="First")
    shipping_profile_2 = ShippingProfileFactory(name="Second")
    customer_1.shipping_profiles.add(shipping_profile_1)
    customer_2.shipping_profiles.add(shipping_profile_2)
    other_customer = CustomerFactory()
    other_customer.shipping_profiles.add(ShippingProfileFactory())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/shipping-profiles")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(profile.id),
                "name": profile.name,
                "phone": profile.phone,
                "address": {
                    "line1": profile.address.line1,
                    "line2": profile.address.line2,
                    "locality": profile.address.locality,
                    "state": profile.address.state,
                    "postal_code": profile.address.postal_code,
                    "country": str(profile.address.country),
                },
                "created_at": ANY,
                "updated_at": ANY,
            }
            for profile in [shipping_profile_2, shipping_profile_1]
        ],
    }


def test_list_shipping_profiles_filter_by_customer(api_client, user, account):
    customer_1 = CustomerFactory(account=account)
    customer_2 = CustomerFactory(account=account)
    shipping_profile = ShippingProfileFactory()
    customer_1.shipping_profiles.add(shipping_profile)
    customer_2.shipping_profiles.add(ShippingProfileFactory())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/shipping-profiles", {"customer_id": str(customer_1.id)})

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(shipping_profile.id)]
    assert response.data["count"] == 1


def test_list_shipping_profiles_requires_authentication(api_client):
    response = api_client.get("/api/v1/shipping-profiles")

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


def test_list_shipping_profiles_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/shipping-profiles")

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
