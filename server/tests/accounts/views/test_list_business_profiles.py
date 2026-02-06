import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, BusinessProfileFactory

pytestmark = pytest.mark.django_db


def test_list_business_profiles(api_client, user, account):
    profile_1 = account.default_business_profile
    profile_2 = BusinessProfileFactory(legal_name="Second")
    account.business_profiles.add(profile_2)
    other_account = AccountFactory()
    other_profile = BusinessProfileFactory(legal_name="Other")
    other_account.business_profiles.add(other_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/business-profiles")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
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
            for profile in [profile_2, profile_1]
        ],
    }


def test_list_business_profiles_requires_authentication(api_client):
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/business-profiles")

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


def test_list_business_profiles_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/business-profiles")

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
