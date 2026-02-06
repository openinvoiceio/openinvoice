import pytest
from freezegun import freeze_time

from openinvoice.portal.crypto import sign_portal_token
from tests.factories import BillingProfileFactory, CustomerFactory, CustomerShippingFactory, PortalTokenFactory

pytestmark = pytest.mark.django_db


def test_retrieve_customer_via_portal(api_client, account):
    shipping = CustomerShippingFactory()
    customer = CustomerFactory(
        account=account,
        name="Old",
        default_billing_profile=BillingProfileFactory(legal_name="Old"),
        shipping=shipping,
    )
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.get("/api/v1/portal/customer", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "name": customer.name,
        "legal_name": customer.default_billing_profile.legal_name,
        "legal_number": customer.default_billing_profile.legal_number,
        "email": customer.default_billing_profile.email,
        "phone": customer.default_billing_profile.phone,
        "address": {
            "line1": customer.default_billing_profile.address.line1,
            "line2": customer.default_billing_profile.address.line2,
            "locality": customer.default_billing_profile.address.locality,
            "state": customer.default_billing_profile.address.state,
            "postal_code": customer.default_billing_profile.address.postal_code,
            "country": customer.default_billing_profile.address.country,
        },
        "shipping": {
            "name": shipping.name,
            "phone": shipping.phone,
            "address": {
                "line1": shipping.address.line1,
                "line2": shipping.address.line2,
                "locality": shipping.address.locality,
                "state": shipping.address.state,
                "postal_code": shipping.address.postal_code,
                "country": shipping.address.country,
            },
        },
        "tax_ids": [],
    }


def test_retrieve_customer_requires_authentication(api_client):
    response = api_client.get("/api/v1/portal/customer")

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


def test_retrieve_customer_with_expired_token(api_client, account):
    customer = CustomerFactory(account=account)

    with freeze_time("2025-01-01 00:00:00"):
        token = sign_portal_token(customer)

    with freeze_time("2025-01-01 12:00:01"):
        response = api_client.get("/api/v1/portal/customer", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "authentication_failed",
                "detail": "Invalid token",
            }
        ],
    }
