import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

pytestmark = pytest.mark.django_db


def test_update_account(api_client, user, account, account_logo):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{account.id}",
        data={
            "name": "New Account Name",
            "legal_name": "New Legal Name",
            "legal_number": "123456789",
            "email": "new@example.com",
            "phone": "123456789",
            "address": {
                "country": "US",
                "line1": "New Line 1",
                "line2": "New Line 2",
                "locality": "New Locality",
                "postal_code": "00-002",
                "state": "New State",
            },
            "country": "US",
            "default_currency": "USD",
            "invoice_footer": "New Footer",
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "net_payment_term": 30,
            "metadata": {"key": "value"},
            "logo_id": account_logo.id,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(account.id),
        "name": "New Account Name",
        "legal_name": "New Legal Name",
        "legal_number": "123456789",
        "email": "new@example.com",
        "phone": "123456789",
        "address": {
            "country": "US",
            "line1": "New Line 1",
            "line2": "New Line 2",
            "locality": "New Locality",
            "postal_code": "00-002",
            "state": "New State",
        },
        "country": "US",
        "default_currency": "USD",
        "invoice_footer": "New Footer",
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "net_payment_term": 30,
        "metadata": {"key": "value"},
        "subscription": None,
        "logo_id": str(account_logo.id),
        "logo_url": f"/media/{account_logo.data.name}",
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_account_logo_not_found(api_client, user, account):
    logo_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{account.id}",
        data={
            "name": "New Account Name",
            "legal_name": "New Legal Name",
            "legal_number": "123456789",
            "email": "new@example.com",
            "phone": "123456789",
            "address": {
                "country": "US",
                "line1": "New Line 1",
                "line2": "New Line 2",
                "locality": "New Locality",
                "postal_code": "00-002",
                "state": "New State",
            },
            "country": "US",
            "default_currency": "USD",
            "invoice_footer": "New Footer",
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "net_payment_term": 30,
            "metadata": {"key": "value"},
            "logo_id": str(logo_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "logo_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{logo_id}" - object does not exist.',
            }
        ],
    }


def test_update_account_requires_authentication(api_client):
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}",
        data={"name": "New Account Name"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_update_account_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}",
        data={"name": "New Account Name"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
