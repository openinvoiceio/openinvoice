from unittest.mock import ANY

import pytest

from tests.factories import BillingProfileFactory, CustomerFactory

pytestmark = pytest.mark.django_db


def test_list_billing_profiles(api_client, user, account):
    customer_1 = CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(legal_name="First"))
    customer_2 = CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(legal_name="Second"))
    CustomerFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/billing-profiles")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(profile.id),
                "legal_name": profile.legal_name,
                "legal_number": profile.legal_number,
                "email": profile.email,
                "phone": profile.phone,
                "address": {
                    "line1": profile.address.line1,
                    "line2": profile.address.line2,
                    "locality": profile.address.locality,
                    "state": profile.address.state,
                    "postal_code": profile.address.postal_code,
                    "country": str(profile.address.country),
                },
                "currency": profile.currency,
                "language": profile.language,
                "net_payment_term": profile.net_payment_term,
                "invoice_numbering_system_id": profile.invoice_numbering_system_id,
                "credit_note_numbering_system_id": profile.credit_note_numbering_system_id,
                "tax_rates": [],
                "tax_ids": [],
                "created_at": ANY,
                "updated_at": ANY,
            }
            for profile in [
                customer_2.default_billing_profile,
                customer_1.default_billing_profile,
            ]
        ],
    }


def test_list_billing_profiles_filter_by_customer(api_client, user, account):
    customer_1 = CustomerFactory(account=account)
    CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/billing-profiles", {"customer_id": str(customer_1.id)})

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(customer_1.default_billing_profile.id)]
    assert response.data["count"] == 1


def test_list_billing_profiles_requires_authentication(api_client):
    response = api_client.get("/api/v1/billing-profiles")

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


def test_list_billing_profiles_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/billing-profiles")

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
