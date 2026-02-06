import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory

pytestmark = pytest.mark.django_db


def test_create_business_profile(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/accounts/{account.id}/business-profiles",
        {
            "legal_name": "New Business",
            "email": "info@example.com",
            "phone": "123",
            "address": {"line1": "Main", "country": "US"},
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "legal_name": "New Business",
        "legal_number": None,
        "email": "info@example.com",
        "phone": "123",
        "address": {
            "line1": "Main",
            "line2": None,
            "locality": None,
            "state": None,
            "postal_code": None,
            "country": "US",
        },
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_business_profile_requires_authentication(api_client):
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/business-profiles",
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


def test_create_business_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/business-profiles",
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


def test_create_business_profile_rejects_foreign_account(api_client, user, account):
    other_account = AccountFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/accounts/{other_account.id}/business-profiles",
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
