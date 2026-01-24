import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import AddressFactory, CustomerFactory, CustomerShippingFactory

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
            "address": {
                "line1": "New Line1",
                "line2": "Line2",
                "locality": "City",
                "postal_code": "00-002",
                "state": "State",
                "country": "US",
            },
            "shipping": {
                "name": "Shipping Name",
                "phone": "111222333",
                "address": {
                    "line1": "Ship Line1",
                    "line2": "Ship Line2",
                    "locality": "Ship City",
                    "postal_code": "00-003",
                    "state": "Ship State",
                    "country": "DE",
                },
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
        "address": {
            "country": "US",
            "line1": "New Line1",
            "line2": "Line2",
            "locality": "City",
            "postal_code": "00-002",
            "state": "State",
        },
        "shipping": {
            "name": "Shipping Name",
            "phone": "111222333",
            "address": {
                "country": "DE",
                "line1": "Ship Line1",
                "line2": "Ship Line2",
                "locality": "Ship City",
                "postal_code": "00-003",
                "state": "Ship State",
            },
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
            "address": {
                "line1": "New Line1",
                "line2": "Line2",
                "locality": "City",
                "postal_code": "00-002",
                "state": "State",
                "country": "US",
            },
            "shipping": {
                "name": "Shipping Name",
                "phone": "111222333",
                "address": {
                    "line1": "Ship Line1",
                    "line2": "Ship Line2",
                    "locality": "Ship City",
                    "postal_code": "00-003",
                    "state": "Ship State",
                    "country": "DE",
                },
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


def test_update_customer_shipping_partial_update(api_client, user, account):
    shipping_address = AddressFactory(line1="Old Line1", country="US")
    shipping = CustomerShippingFactory(name="Original", phone="123", address=shipping_address)
    customer = CustomerFactory(account=account, shipping=shipping)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={
            "shipping": {
                "phone": "999",
                "address": {"line1": "Partial"},
            }
        },
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is not None
    assert customer.shipping.name == "Original"
    assert customer.shipping.phone == "999"
    assert customer.shipping.address.line1 == "Partial"
    assert customer.shipping.address.country == "US"


def test_update_customer_remove_shipping(api_client, user, account):
    shipping = CustomerShippingFactory()
    customer = CustomerFactory(account=account, shipping=shipping)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={"shipping": None},
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is None


def test_update_customer_remove_missing_shipping(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={"shipping": None},
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is None


def test_update_customer_add_shipping(api_client, user, account):
    customer = CustomerFactory(account=account, shipping=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/customers/{customer.id}",
        data={
            "shipping": {
                "name": "New Ship",
                "phone": "555",
                "address": {"line1": "Ship Line", "country": "US"},
            }
        },
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is not None
    assert customer.shipping.name == "New Ship"
    assert customer.shipping.phone == "555"
    assert customer.shipping.address.line1 == "Ship Line"
    assert customer.shipping.address.country == "US"
