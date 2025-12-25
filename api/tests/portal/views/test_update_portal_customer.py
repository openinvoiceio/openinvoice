import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import (
    CustomerFactory,
    PortalTokenFactory,
)

pytestmark = pytest.mark.django_db


def test_update_customer_via_portal(api_client, account):
    customer = CustomerFactory(account=account, name="Old")
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {
            "name": "New",
            "email": "new@example.com",
            "phone": "123",
            "legal_name": "LN",
            "legal_number": "42",
            "billing_address": {"line1": "New line1"},
            "shipping_address": {"country": "US"},
        },
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "name": "New",
        "legal_name": "LN",
        "legal_number": "42",
        "email": "new@example.com",
        "phone": "123",
        "billing_address": {
            "line1": "New line1",
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
            "country": "US",
        },
        "tax_ids": [],
    }


def test_update_customer_requires_authentication(api_client):
    response = api_client.put("/api/v1/portal/customer", {"name": "New"})

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
