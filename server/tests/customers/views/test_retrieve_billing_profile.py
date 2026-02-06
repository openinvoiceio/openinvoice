import uuid
from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_retrieve_billing_profile(api_client, user, account):
    customer = CustomerFactory(account=account)
    billing_profile = customer.default_billing_profile

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/billing-profiles/{billing_profile.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(billing_profile.id),
        "legal_name": billing_profile.legal_name,
        "legal_number": billing_profile.legal_number,
        "email": billing_profile.email,
        "phone": billing_profile.phone,
        "address": {
            "line1": billing_profile.address.line1,
            "line2": billing_profile.address.line2,
            "locality": billing_profile.address.locality,
            "state": billing_profile.address.state,
            "postal_code": billing_profile.address.postal_code,
            "country": str(billing_profile.address.country),
        },
        "currency": billing_profile.currency,
        "language": billing_profile.language,
        "net_payment_term": billing_profile.net_payment_term,
        "invoice_numbering_system_id": billing_profile.invoice_numbering_system_id,
        "credit_note_numbering_system_id": billing_profile.credit_note_numbering_system_id,
        "tax_rates": [],
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_retrieve_billing_profile_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/billing-profiles/{uuid.uuid4()}")

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


def test_retrieve_billing_profile_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.get(f"/api/v1/billing-profiles/{customer.default_billing_profile.id}")

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


def test_retrieve_billing_profile_requires_account(api_client, user):
    customer = CustomerFactory()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/billing-profiles/{customer.default_billing_profile.id}")

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


def test_retrieve_billing_profile_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/billing-profiles/{customer.default_billing_profile.id}")

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
