import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, AddressFactory

pytestmark = pytest.mark.django_db


def test_list_account_addresses(api_client, user, account):
    address_1 = AddressFactory(line1="Alpha", country="US")
    address_2 = AddressFactory(line1="Beta", country="PL")
    account.addresses.add(address_1, address_2)
    other_account = AccountFactory()
    other_account.addresses.add(AddressFactory(line1="Other", country="US"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/addresses")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(address.id),
                "line1": address.line1,
                "line2": address.line2,
                "locality": address.locality,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": str(address.country) if address.country else None,
                "created_at": ANY,
                "updated_at": ANY,
            }
            for address in [address_2, address_1]
        ],
    }


def test_list_account_addresses_not_found(api_client, user, account):
    other_account = AccountFactory()
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.get(f"/api/v1/accounts/{other_account.id}/addresses")

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


def test_list_account_addresses_requires_authentication(api_client):
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/addresses")

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


def test_list_account_addresses_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/addresses")

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
