import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory

pytestmark = pytest.mark.django_db


def test_create_account_address(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/accounts/{account.id}/addresses",
        {"line1": "Main", "locality": "Town", "country": "US"},
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "line1": "Main",
        "line2": None,
        "locality": "Town",
        "state": None,
        "postal_code": None,
        "country": "US",
        "created_at": ANY,
        "updated_at": ANY,
    }
    assert account.addresses.count() == 1


def test_create_account_address_invalid_country(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/accounts/{account.id}/addresses",
        {"line1": "Main", "country": "XX"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "country",
                "code": "invalid_choice",
                "detail": '"XX" is not a valid choice.',
            }
        ],
    }


def test_create_account_address_not_found(api_client, user, account):
    other_account = AccountFactory()
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        f"/api/v1/accounts/{other_account.id}/addresses",
        {"line1": "Main", "locality": "Town", "country": "US"},
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


def test_create_account_address_requires_authentication(api_client):
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/addresses",
        {"line1": "Main", "locality": "Town", "country": "US"},
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


def test_create_account_address_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/addresses",
        {"line1": "Main", "locality": "Town", "country": "US"},
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
