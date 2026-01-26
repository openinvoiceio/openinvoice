import uuid
from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_retrieve_customer(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/customers/{customer.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "account_id": str(customer.account_id),
        "name": customer.name,
        "legal_name": customer.legal_name,
        "legal_number": customer.legal_number,
        "email": customer.email,
        "phone": customer.phone,
        "currency": customer.currency,
        "net_payment_term": customer.net_payment_term,
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "description": customer.description,
        "metadata": customer.metadata,
        "address": {
            "country": customer.address.country,
            "line1": customer.address.line1,
            "line2": customer.address.line2,
            "locality": customer.address.locality,
            "postal_code": customer.address.postal_code,
            "state": customer.address.state,
        },
        "shipping": None,
        "tax_rates": [],
        "tax_ids": [],
        "logo_id": None,
        "logo_url": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_retrieve_customer_requires_account(api_client, user):
    customer = CustomerFactory()
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/customers/{customer.id}")

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


def test_retrieve_customer_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/customers/{uuid.uuid4()}")

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


def test_retrieve_customer_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.get(f"/api/v1/customers/{customer.id}")

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


def test_retrieve_customer_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/customers/{customer.id}")

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
