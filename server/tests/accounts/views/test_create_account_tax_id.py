import uuid
from unittest.mock import ANY

import pytest
from django.conf import settings

from tests.factories import AccountFactory, TaxIdFactory

pytestmark = pytest.mark.django_db


def test_create_account_tax_id(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/accounts/{account.id}/tax-ids",
        {"type": "us_ein", "number": "123456789"},
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "type": "us_ein",
        "number": "123456789",
        "country": None,
        "created_at": ANY,
        "updated_at": ANY,
    }
    assert account.tax_ids.count() == 1


def test_create_account_tax_id_limit(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    for _ in range(settings.MAX_TAX_IDS):
        account.tax_ids.add(TaxIdFactory())

    response = api_client.post(
        f"/api/v1/accounts/{account.id}/tax-ids",
        {"type": "us_ein", "number": "123"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "You can add at most 5 tax IDs to an account.",
            }
        ],
    }


def test_create_account_tax_id_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    other_account = AccountFactory()
    response = api_client.post(
        f"/api/v1/accounts/{other_account.id}/tax-ids",
        {"type": "us_ein", "number": "123"},
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


def test_create_account_tax_id_requires_authentication(api_client):
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/tax-ids",
        {"type": "us_ein", "number": "123456789"},
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


def test_create_account_tax_id_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/accounts/{uuid.uuid4()}/tax-ids",
        {"type": "us_ein", "number": "123456789"},
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
