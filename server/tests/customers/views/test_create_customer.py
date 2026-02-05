import uuid
from unittest.mock import ANY

import pytest

from openinvoice.core.choices import LimitCode
from openinvoice.customers.models import Customer

pytestmark = pytest.mark.django_db


def test_create_customer(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/customers",
        data={
            "billing_profile": {
                "name": "Customer 1",
                "legal_name": "Customer One LLC",
                "legal_number": "CUST-001",
                "email": "customer1@example.com",
                "phone": "123456789",
                "currency": "USD",
                "net_payment_term": 15,
                "invoice_numbering_system_id": None,
                "credit_note_numbering_system_id": None,
                "address": {"line1": "123", "country": "PL"},
            },
            "shipping_profile": {
                "name": "Customer Shipping",
                "phone": "987654321",
                "address": {"line1": "321", "country": "PL"},
            },
            "description": "Important customer",
            "metadata": {"note": "value"},
            "logo_id": None,
        },
    )

    assert response.status_code == 201
    customer = Customer.objects.get(id=response.data["id"])
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "description": "Important customer",
        "metadata": {"note": "value"},
        "default_billing_profile": {
            "id": str(customer.default_billing_profile.id),
            "name": "Customer 1",
            "legal_name": "Customer One LLC",
            "legal_number": "CUST-001",
            "email": "customer1@example.com",
            "phone": "123456789",
            "address": {
                "line1": "123",
                "line2": None,
                "locality": None,
                "state": None,
                "postal_code": None,
                "country": "PL",
            },
            "currency": "USD",
            "language": customer.default_billing_profile.language,
            "net_payment_term": 15,
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "default_shipping_profile": {
            "id": str(customer.default_shipping_profile.id),
            "name": "Customer Shipping",
            "phone": "987654321",
            "address": {
                "line1": "321",
                "line2": None,
                "locality": None,
                "state": None,
                "postal_code": None,
                "country": "PL",
            },
            "created_at": ANY,
            "updated_at": ANY,
        },
        "logo_id": None,
        "logo_url": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_customer_logo_not_found(api_client, user, account):
    logo_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/customers",
        data={
            "billing_profile": {"name": "Customer 1"},
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


def test_create_customer_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_CUSTOMERS: 0}}}

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/customers",
        data={"billing_profile": {"name": "Another"}},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }


def test_create_customer_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/customers",
        data={"billing_profile": {"name": "NoAccount"}},
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


def test_create_customer_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/customers",
        data={"billing_profile": {"name": "Customer"}},
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
