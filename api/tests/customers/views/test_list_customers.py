from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.customers.models import Customer
from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_list_customers(api_client, user, account):
    customer_1 = CustomerFactory(account=account, name="Customer 1")
    customer_2 = CustomerFactory(account=account, name="Customer 2")
    CustomerFactory()  # another account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
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
            "billing_address": {
                "country": customer.billing_address.country,
                "line1": customer.billing_address.line1,
                "line2": customer.billing_address.line2,
                "locality": customer.billing_address.locality,
                "postal_code": customer.billing_address.postal_code,
                "state": customer.billing_address.state,
            },
            "shipping_address": {
                "country": customer.shipping_address.country,
                "line1": customer.shipping_address.line1,
                "line2": customer.shipping_address.line2,
                "locality": customer.shipping_address.locality,
                "postal_code": customer.shipping_address.postal_code,
                "state": customer.shipping_address.state,
            },
            "tax_rates": [],
            "tax_ids": [],
            "logo_id": None,
            "logo_url": None,
            "created_at": ANY,
            "updated_at": ANY,
        }
        for customer in [customer_2, customer_1]
    ]


def test_list_customers_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/customers")

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


def test_list_customers_requires_authentication(api_client, account):
    CustomerFactory(account=account)

    response = api_client.get("/api/v1/customers")

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


def test_list_customers_filter_by_currency(api_client, user, account):
    usd = CustomerFactory(account=account, currency="USD")
    CustomerFactory(account=account, currency="EUR")
    pln = CustomerFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"currency": "USD,PLN"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [
        str(pln.id),
        str(usd.id),
    ]


def test_list_customers_filter_created_at_after(api_client, user, account):
    base = timezone.now()
    older = CustomerFactory(account=account)
    Customer.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"created_at_after": (base - timedelta(hours=12)).isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_customers_filter_created_at_before(api_client, user, account):
    base = timezone.now()
    older = CustomerFactory(account=account)
    Customer.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_customers_rejects_foreign_account(api_client, user, account):
    owned = CustomerFactory(account=account)
    CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers")

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(owned.id)]


def test_list_customers_search_by_name(api_client, user, account):
    CustomerFactory(account=account, name="Alice")
    CustomerFactory(account=account, name="Bob")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "Alice"})

    assert response.status_code == 200
    assert [r["name"] for r in response.data["results"]] == ["Alice"]


def test_list_customers_search_by_email(api_client, user, account):
    CustomerFactory(account=account, email="a@example.com")
    CustomerFactory(account=account, email="b@example.com")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "a@example.com"})

    assert response.status_code == 200
    assert [r["email"] for r in response.data["results"]] == ["a@example.com"]


def test_list_customers_search_by_phone(api_client, user, account):
    CustomerFactory(account=account, phone="111")
    CustomerFactory(account=account, phone="222")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "111"})

    assert response.status_code == 200
    assert [r["phone"] for r in response.data["results"]] == ["111"]


def test_list_customers_search_by_description(api_client, user, account):
    CustomerFactory(account=account, description="desc1")
    CustomerFactory(account=account, description="desc2")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "desc1"})

    assert response.status_code == 200
    assert [r["description"] for r in response.data["results"]] == ["desc1"]


def test_list_customers_order_by_created_at(api_client, user, account):
    older = CustomerFactory(account=account, name="Older")
    newer = CustomerFactory(account=account, name="Newer")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"ordering": "created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(older.id),
        str(newer.id),
    ]


def test_list_customers_order_by_created_at_desc(api_client, user, account):
    older = CustomerFactory(account=account, name="Older")
    newer = CustomerFactory(account=account, name="Newer")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"ordering": "-created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(newer.id),
        str(older.id),
    ]
