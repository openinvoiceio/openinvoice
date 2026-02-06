import uuid

import pytest

from tests.factories import BillingProfileFactory, CustomerFactory

pytestmark = pytest.mark.django_db


def test_delete_billing_profile(api_client, user, account):
    customer = CustomerFactory(account=account)
    billing_profile = BillingProfileFactory()
    customer.billing_profiles.add(billing_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/billing-profiles/{billing_profile.id}")

    assert response.status_code == 204


def test_delete_billing_profile_default_for_customer(api_client, user, account):
    customer = CustomerFactory(account=account)
    billing_profile = customer.default_billing_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/billing-profiles/{billing_profile.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Default billing profiles cannot be deleted",
            }
        ],
    }


def test_delete_billing_profile_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/billing-profiles/{uuid.uuid4()}")

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


def test_delete_billing_profile_requires_authentication(api_client):
    response = api_client.delete(f"/api/v1/billing-profiles/{uuid.uuid4()}")

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


def test_delete_billing_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/billing-profiles/{uuid.uuid4()}")

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


def test_delete_billing_profile_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()
    billing_profile = customer.default_billing_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/billing-profiles/{billing_profile.id}")

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
