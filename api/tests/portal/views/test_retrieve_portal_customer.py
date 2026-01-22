import pytest
from drf_standardized_errors.types import ErrorType
from freezegun import freeze_time

from apps.portal.crypto import sign_portal_token
from tests.factories import (
    CustomerFactory,
    PortalTokenFactory,
)

pytestmark = pytest.mark.django_db


def test_retrieve_customer_via_portal(api_client, account):
    customer = CustomerFactory(account=account, name="Old")
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.get("/api/v1/portal/customer", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "name": customer.name,
        "legal_name": customer.legal_name,
        "legal_number": customer.legal_number,
        "email": customer.email,
        "phone": customer.phone,
        "billing_address": {
            "line1": customer.billing_address.line1,
            "line2": customer.billing_address.line2,
            "locality": customer.billing_address.locality,
            "state": customer.billing_address.state,
            "postal_code": customer.billing_address.postal_code,
            "country": customer.billing_address.country,
        },
        "shipping_address": {
            "line1": customer.shipping_address.line1,
            "line2": customer.shipping_address.line2,
            "locality": customer.shipping_address.locality,
            "state": customer.shipping_address.state,
            "postal_code": customer.shipping_address.postal_code,
            "country": customer.shipping_address.country,
        },
        "tax_ids": [],
    }


def test_retrieve_customer_requires_authentication(api_client):
    response = api_client.get("/api/v1/portal/customer")

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


def test_retrieve_customer_with_expired_token(api_client, account):
    customer = CustomerFactory(account=account)

    with freeze_time("2025-01-01 00:00:00"):
        token = sign_portal_token(customer)

    with freeze_time("2025-01-01 12:00:01"):
        response = api_client.get("/api/v1/portal/customer", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "authentication_failed",
                "detail": "Invalid token",
            }
        ],
    }
