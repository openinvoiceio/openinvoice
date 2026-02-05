from unittest.mock import ANY

import pytest

from tests.factories import AccountFactory, BusinessProfileFactory, MemberFactory

pytestmark = pytest.mark.django_db


def test_list_accounts(api_client, user):
    account_1 = AccountFactory(default_business_profile=BusinessProfileFactory(name="Account 1"))
    account_2 = AccountFactory(default_business_profile=BusinessProfileFactory(name="Account 2"))
    AccountFactory(default_business_profile=BusinessProfileFactory(name="Account 3"))
    MemberFactory(user=user, account=account_1)
    MemberFactory(user=user, account=account_2)

    api_client.force_login(user)
    response = api_client.get("/api/v1/accounts")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
            "id": str(account.id),
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
        for account in [account_2, account_1]
    ]


def test_list_accounts_requires_authentication(api_client):
    response = api_client.get("/api/v1/accounts")

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
