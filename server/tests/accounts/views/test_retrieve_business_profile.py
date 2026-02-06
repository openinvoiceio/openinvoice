import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory

pytestmark = pytest.mark.django_db


def test_retrieve_business_profile(api_client, user, account):
    profile = account.default_business_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/business-profiles/{profile.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(profile.id),
        "legal_name": profile.legal_name,
        "legal_number": profile.legal_number,
        "email": profile.email,
        "phone": profile.phone,
        "address": {
            "line1": profile.address.line1,
            "line2": profile.address.line2,
            "locality": profile.address.locality,
            "state": profile.address.state,
            "postal_code": profile.address.postal_code,
            "country": str(profile.address.country),
        },
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_retrieve_business_profile_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/business-profiles/{uuid.uuid4()}")

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


def test_retrieve_business_profile_requires_authentication(api_client, account):
    profile = account.default_business_profile

    response = api_client.get(f"/api/v1/accounts/{account.id}/business-profiles/{profile.id}")

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


def test_retrieve_business_profile_requires_account(api_client, user):
    account = AccountFactory()
    profile = account.default_business_profile

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{account.id}/business-profiles/{profile.id}")

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


def test_retrieve_business_profile_rejects_foreign_account(api_client, user, account):
    other_account = AccountFactory()
    profile = other_account.default_business_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{other_account.id}/business-profiles/{profile.id}")

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
