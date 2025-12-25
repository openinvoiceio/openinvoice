from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import AccountFactory, MemberFactory

pytestmark = pytest.mark.django_db


def test_list_accounts(api_client, user):
    account_1 = AccountFactory(name="Account 1")
    account_2 = AccountFactory(name="Account 2")
    AccountFactory(name="Account 3")
    MemberFactory(user=user, account=account_1)
    MemberFactory(user=user, account=account_2)

    api_client.force_login(user)
    response = api_client.get("/api/v1/accounts")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
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
        for account in [account_2, account_1]
    ]


def test_list_accounts_requires_authentication(api_client):
    response = api_client.get("/api/v1/accounts")

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
