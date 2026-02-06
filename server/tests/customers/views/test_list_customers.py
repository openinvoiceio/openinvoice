from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone

from openinvoice.customers.models import Customer
from tests.factories import BillingProfileFactory, CustomerFactory

pytestmark = pytest.mark.django_db


def test_list_customers(api_client, user, account):
    customer_1 = CustomerFactory(
        account=account,
        name="Customer 1",
        default_billing_profile=BillingProfileFactory(legal_name="Customer 1"),
    )
    customer_2 = CustomerFactory(
        account=account,
        name="Customer 2",
        default_billing_profile=BillingProfileFactory(legal_name="Customer 2"),
    )
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
            "description": customer.description,
            "metadata": customer.metadata,
            "default_billing_profile": {
                "id": str(customer.default_billing_profile.id),
                "legal_name": customer.default_billing_profile.legal_name,
                "legal_number": customer.default_billing_profile.legal_number,
                "email": customer.default_billing_profile.email,
                "phone": customer.default_billing_profile.phone,
                "address": {
                    "line1": customer.default_billing_profile.address.line1,
                    "line2": customer.default_billing_profile.address.line2,
                    "locality": customer.default_billing_profile.address.locality,
                    "state": customer.default_billing_profile.address.state,
                    "postal_code": customer.default_billing_profile.address.postal_code,
                    "country": str(customer.default_billing_profile.address.country),
                },
                "currency": customer.default_billing_profile.currency,
                "language": customer.default_billing_profile.language,
                "net_payment_term": customer.default_billing_profile.net_payment_term,
                "invoice_numbering_system_id": customer.default_billing_profile.invoice_numbering_system_id,
                "credit_note_numbering_system_id": customer.default_billing_profile.credit_note_numbering_system_id,
                "tax_rates": [],
                "tax_ids": [],
                "created_at": ANY,
                "updated_at": ANY,
            },
            "default_shipping_profile": None,
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
        "type": "client_error",
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
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_list_customers_filter_by_currency(api_client, user, account):
    usd = CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(currency="USD"))
    CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(currency="EUR"))
    pln = CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(currency="PLN"))

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
    CustomerFactory(account=account, name="Alice", default_billing_profile=BillingProfileFactory(legal_name="Alice"))
    CustomerFactory(account=account, name="Bob", default_billing_profile=BillingProfileFactory(legal_name="Bob"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "Alice"})

    assert response.status_code == 200
    assert [r["name"] for r in response.data["results"]] == ["Alice"]


def test_list_customers_search_by_email(api_client, user, account):
    CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(email="a@example.com"))
    CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(email="b@example.com"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "a@example.com"})

    assert response.status_code == 200
    assert [r["default_billing_profile"]["email"] for r in response.data["results"]] == ["a@example.com"]


def test_list_customers_search_by_phone(api_client, user, account):
    CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(phone="111"))
    CustomerFactory(account=account, default_billing_profile=BillingProfileFactory(phone="222"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "111"})

    assert response.status_code == 200
    assert [r["default_billing_profile"]["phone"] for r in response.data["results"]] == ["111"]


def test_list_customers_search_by_description(api_client, user, account):
    CustomerFactory(account=account, description="desc1")
    CustomerFactory(account=account, description="desc2")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"search": "desc1"})

    assert response.status_code == 200
    assert [r["description"] for r in response.data["results"]] == ["desc1"]


def test_list_customers_order_by_created_at(api_client, user, account):
    older = CustomerFactory(
        account=account, name="Older", default_billing_profile=BillingProfileFactory(legal_name="Older")
    )
    newer = CustomerFactory(
        account=account, name="Newer", default_billing_profile=BillingProfileFactory(legal_name="Newer")
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"ordering": "created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(older.id),
        str(newer.id),
    ]


def test_list_customers_order_by_created_at_desc(api_client, user, account):
    older = CustomerFactory(
        account=account, name="Older", default_billing_profile=BillingProfileFactory(legal_name="Older")
    )
    newer = CustomerFactory(
        account=account, name="Newer", default_billing_profile=BillingProfileFactory(legal_name="Newer")
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/customers", {"ordering": "-created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(newer.id),
        str(older.id),
    ]
