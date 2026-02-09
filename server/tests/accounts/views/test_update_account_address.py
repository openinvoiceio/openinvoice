import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, AddressFactory

pytestmark = pytest.mark.django_db


def test_update_account_address(api_client, user, account):
    address = AddressFactory(line1="Main", country="US")
    account.addresses.add(address)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{account.id}/addresses/{address.id}",
        {"line1": "Updated", "locality": "Town", "country": "PL"},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(address.id),
        "line1": "Updated",
        "line2": address.line2,
        "locality": "Town",
        "state": address.state,
        "postal_code": address.postal_code,
        "country": "PL",
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_account_address_not_found(api_client, user, account):
    other_account = AccountFactory()
    address = AddressFactory(line1="Main", country="US")
    other_account.addresses.add(address)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{account.id}/addresses/{address.id}",
        {"line1": "Updated", "country": "US"},
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


def test_update_account_address_account_not_found(api_client, user, account):
    address = AddressFactory(line1="Main", country="US")
    account.addresses.add(address)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}/addresses/{address.id}",
        {"line1": "Updated", "country": "US"},
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


def test_update_account_address_requires_authentication(api_client):
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}/addresses/{uuid.uuid4()}",
        {"line1": "Updated", "country": "US"},
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


def test_update_account_address_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}/addresses/{uuid.uuid4()}",
        {"line1": "Updated", "country": "US"},
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
