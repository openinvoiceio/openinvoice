import uuid

import pytest

from tests.factories import AccountFactory, AddressFactory, BusinessProfileFactory

pytestmark = pytest.mark.django_db


def test_delete_account_address(api_client, user, account):
    address = AddressFactory()
    account.addresses.add(address)
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/accounts/{account.id}/addresses/{address.id}")

    assert response.status_code == 204
    assert account.addresses.count() == 0


def test_delete_account_address_protected(api_client, user, account):
    address = AddressFactory()
    profile = BusinessProfileFactory(address=address)
    account.business_profiles.add(profile)
    account.addresses.add(address)
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/accounts/{account.id}/addresses/{address.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "This object cannot be deleted because it has related data.",
            }
        ],
    }


def test_delete_account_address_not_found(api_client, user, account):
    other_account = AccountFactory()
    address = AddressFactory()
    other_account.addresses.add(address)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/accounts/{account.id}/addresses/{address.id}")

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


def test_delete_account_address_account_not_found(api_client, user, account):
    address = AddressFactory()
    account.addresses.add(address)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}/addresses/{address.id}")

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


def test_delete_account_address_requires_authentication(api_client):
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}/addresses/{uuid.uuid4()}")

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


def test_delete_account_address_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}/addresses/{uuid.uuid4()}")

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
