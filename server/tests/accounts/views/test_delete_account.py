import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, MemberFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_delete_account(api_client, user):
    account = AccountFactory(name="Account to Delete")
    MemberFactory(user=user, account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/accounts/{account.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(account.id),
        "name": account.name,
        "legal_name": account.legal_name,
        "legal_number": account.legal_number,
        "email": account.email,
        "phone": account.phone,
        "address": {
            "country": account.address.country,
            "line1": account.address.line1,
            "line2": account.address.line2,
            "locality": account.address.locality,
            "postal_code": account.address.postal_code,
            "state": account.address.state,
        },
        "country": str(account.country),
        "default_currency": account.default_currency,
        "language": account.language,
        "invoice_footer": account.invoice_footer,
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "net_payment_term": account.net_payment_term,
        "metadata": account.metadata,
        "subscription": None,
        "logo_id": None,
        "logo_url": None,
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }

    response = api_client.delete(f"/api/v1/accounts/{account.id}")
    assert response.status_code == 403


def test_delete_account_with_members(api_client, user, account):
    email = "test@example.com"
    user_2 = UserFactory(email=email, username=email, name="Test User")
    MemberFactory(user=user_2, account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/accounts/{account.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Account has members and cannot be deleted.",
            }
        ],
    }


def test_delete_account_requires_authentication(api_client):
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}")

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


def test_delete_account_requires_account(api_client, account):
    other_user = UserFactory(email="test@example.com", username="test")

    api_client.force_login(other_user)
    response = api_client.delete(f"/api/v1/accounts/{account.id}")

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
