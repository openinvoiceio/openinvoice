import uuid
from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, MemberFactory

pytestmark = pytest.mark.django_db


def test_retrieve_account(api_client, user):
    account = AccountFactory(name="Test Account")
    MemberFactory(user=user, account=account)

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{account.id}")

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


def test_retrieve_account_requires_authentication(api_client, account):
    response = api_client.get(f"/api/v1/accounts/{account.id}")

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


def test_retrieve_account_requires_account(api_client, user):
    account_id = str(uuid.uuid4())

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{account_id}")

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
