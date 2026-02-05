import uuid
from unittest.mock import ANY

import pytest

pytestmark = pytest.mark.django_db


def test_update_account(api_client, user, account, account_logo):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/accounts/{account.id}",
        data={
            "country": "US",
            "default_currency": "USD",
            "language": "en-us",
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
        "country": "US",
        "default_currency": "USD",
        "language": "en-us",
        "invoice_footer": "New Footer",
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "net_payment_term": 30,
        "metadata": {"key": "value"},
        "subscription": None,
        "logo_id": str(account_logo.id),
        "logo_url": f"http://testserver/media/{account_logo.data.name}",
        "default_business_profile": {
            "id": str(account.default_business_profile.id),
            "name": account.default_business_profile.name,
            "legal_name": account.default_business_profile.legal_name,
            "legal_number": account.default_business_profile.legal_number,
            "email": account.default_business_profile.email,
            "phone": account.default_business_profile.phone,
            "address": {
                "line1": account.default_business_profile.address.line1,
                "line2": account.default_business_profile.address.line2,
                "locality": account.default_business_profile.address.locality,
                "state": account.default_business_profile.address.state,
                "postal_code": account.default_business_profile.address.postal_code,
                "country": str(account.default_business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
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
        "type": "validation_error",
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
        data={"country": "US"},
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


def test_update_account_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/accounts/{uuid.uuid4()}",
        data={"country": "US"},
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
