import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_update_customer(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={
            "name": "New Name",
            "legal_name": "Legal Name",
            "legal_number": "LN-999",
            "email": "new@example.com",
            "phone": "999",
            "description": "New description",
            "currency": "EUR",
            "net_payment_term": 30,
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "metadata": {"key": "value"},
            "billing_address": {
                "line1": "New Line1",
                "line2": "Line2",
                "locality": "City",
                "postal_code": "00-002",
                "state": "State",
                "country": "US",
            },
            "shipping_address": {
                "line1": "Ship Line1",
                "line2": "Ship Line2",
                "locality": "Ship City",
                "postal_code": "00-003",
                "state": "Ship State",
                "country": "DE",
            },
            "logo_id": None,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "account_id": str(customer.account_id),
        "name": "New Name",
        "legal_name": "Legal Name",
        "legal_number": "LN-999",
        "email": "new@example.com",
        "phone": "999",
        "currency": "EUR",
        "net_payment_term": 30,
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "description": "New description",
        "metadata": {"key": "value"},
        "billing_address": {
            "country": "US",
            "line1": "New Line1",
            "line2": "Line2",
            "locality": "City",
            "postal_code": "00-002",
            "state": "State",
        },
        "shipping_address": {
            "country": "DE",
            "line1": "Ship Line1",
            "line2": "Ship Line2",
            "locality": "Ship City",
            "postal_code": "00-003",
            "state": "Ship State",
        },
        "tax_rates": [],
        "tax_ids": [],
        "logo_id": None,
        "logo_url": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_customer_logo_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)
    logo_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={
            "name": "New Name",
            "legal_name": "Legal Name",
            "legal_number": "LN-999",
            "email": "new@example.com",
            "phone": "999",
            "description": "New description",
            "currency": "EUR",
            "net_payment_term": 30,
            "invoice_numbering_system_id": None,
            "credit_note_numbering_system_id": None,
            "metadata": {"key": "value"},
            "billing_address": {
                "line1": "New Line1",
                "line2": "Line2",
                "locality": "City",
                "postal_code": "00-002",
                "state": "State",
                "country": "US",
            },
            "shipping_address": {
                "line1": "Ship Line1",
                "line2": "Ship Line2",
                "locality": "Ship City",
                "postal_code": "00-003",
                "state": "Ship State",
                "country": "DE",
            },
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


def test_update_customer_requires_account(api_client, user):
    customer = CustomerFactory()
    api_client.force_login(user)
    response = api_client.put(f"/api/v1/customers/{customer.id}", data={"name": "New"})

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


def test_update_customer_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.put(f"/api/v1/customers/{customer.id}", data={"name": "New"})

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


def test_update_customer_rejects_foreign_account(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(f"/api/v1/customers/{customer.id}", data={"name": "New"})

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }
