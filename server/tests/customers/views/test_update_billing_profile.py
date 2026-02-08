import uuid
from unittest.mock import ANY

import pytest

from tests.factories import BillingProfileFactory, CustomerFactory

pytestmark = pytest.mark.django_db


def test_update_billing_profile(api_client, user, account):
    customer = CustomerFactory(account=account)
    billing_profile = BillingProfileFactory(legal_name="Old")
    customer.billing_profiles.add(billing_profile)
    line2 = billing_profile.address.line2
    state = billing_profile.address.state
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/billing-profiles/{billing_profile.id}",
        {
            "legal_name": "New Legal",
            "email": "billing@example.com",
            "phone": "555-111",
            "address": {
                "line1": "123 Road",
                "locality": "City",
                "postal_code": "12345",
                "country": "US",
            },
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(billing_profile.id),
        "legal_name": "New Legal",
        "legal_number": billing_profile.legal_number,
        "email": "billing@example.com",
        "phone": "555-111",
        "address": {
            "line1": "123 Road",
            "line2": line2,
            "locality": "City",
            "state": state,
            "postal_code": "12345",
            "country": "US",
        },
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_billing_profile_requires_authentication(api_client):
    response = api_client.put(
        f"/api/v1/billing-profiles/{uuid.uuid4()}",
        {"legal_name": "Name"},
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


def test_update_billing_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/billing-profiles/{uuid.uuid4()}",
        {"legal_name": "Name"},
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


def test_update_billing_profile_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()
    billing_profile = customer.default_billing_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/billing-profiles/{billing_profile.id}",
        {"legal_name": "Name"},
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
