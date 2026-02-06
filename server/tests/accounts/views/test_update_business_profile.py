import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, BusinessProfileFactory, TaxIdFactory

pytestmark = pytest.mark.django_db


def test_update_business_profile(api_client, user, account):
    profile = BusinessProfileFactory(legal_name="Old")
    account.business_profiles.add(profile)
    line2 = profile.address.line2
    state = profile.address.state

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/business-profiles/{profile.id}",
        {
            "legal_name": "New",
            "email": "info@example.com",
            "phone": "555",
            "address": {
                "line1": "Main",
                "locality": "Town",
                "postal_code": "123",
                "country": "US",
            },
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(profile.id),
        "legal_name": "New",
        "legal_number": profile.legal_number,
        "email": "info@example.com",
        "phone": "555",
        "address": {
            "line1": "Main",
            "line2": line2,
            "locality": "Town",
            "state": state,
            "postal_code": "123",
            "country": "US",
        },
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_business_profile_tax_ids(api_client, user, account):
    profile = BusinessProfileFactory()
    account.business_profiles.add(profile)
    tax_id = TaxIdFactory()
    account.tax_ids.add(tax_id)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/business-profiles/{profile.id}",
        {
            "tax_ids": [str(tax_id.id)],
        },
    )

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
        "tax_ids": [
            {
                "id": str(tax_id.id),
                "type": tax_id.type,
                "number": tax_id.number,
                "country": tax_id.country,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_business_profile_requires_authentication(api_client):
    response = api_client.put(
        f"/api/v1/business-profiles/{uuid.uuid4()}",
        {"legal_name": "New"},
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


def test_update_business_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/business-profiles/{uuid.uuid4()}",
        {"legal_name": "New"},
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


def test_update_business_profile_rejects_foreign_account(api_client, user, account):
    other_account = AccountFactory()
    profile = other_account.default_business_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/business-profiles/{profile.id}",
        {"legal_name": "New"},
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
