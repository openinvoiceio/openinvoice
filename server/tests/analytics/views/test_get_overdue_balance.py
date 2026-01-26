from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from openinvoice.invoices.choices import InvoiceStatus
from tests.factories import CustomerFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-01-01")
def test_get_overdue_balance(api_client, user, account):
    past_due = date(2024, 12, 1)
    inv_pln = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=past_due,
        total_amount=Decimal("20"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="USD",
        due_date=past_due,
        total_amount=Decimal("30"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=date(2025, 1, 15),
        total_amount=Decimal("40"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/overdue-balance")

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "20.00", "invoice_ids": [str(inv_pln.id)]},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
    ]


@freeze_time("2025-01-01")
def test_get_overdue_balance_filter_currency(api_client, user, account):
    past_due = date(2024, 12, 1)
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="USD",
        due_date=past_due,
        total_amount=Decimal("20"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="EUR",
        due_date=past_due,
        total_amount=Decimal("30"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/overdue-balance", {"currency": "EUR"})

    assert response.status_code == 200
    assert all(item["currency"] == "EUR" for item in response.data)


@freeze_time("2025-01-01")
def test_get_overdue_balance_filter_date_after(api_client, user, account):
    inv = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=date(2024, 12, 1),
        total_amount=Decimal("10"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=date(2024, 11, 1),
        total_amount=Decimal("20"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/overdue-balance", {"date_after": date(2024, 12, 1).isoformat()})

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "10.00", "invoice_ids": [str(inv.id)]},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
    ]


@freeze_time("2025-01-01")
def test_get_overdue_balance_filter_date_before(api_client, user, account):
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=date(2024, 12, 1),
        total_amount=Decimal("10"),
    )
    inv = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=date(2024, 11, 1),
        total_amount=Decimal("20"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/analytics/overdue-balance",
        {"date_before": date(2024, 11, 30).isoformat()},
    )

    assert response.status_code == 200
    assert response.data == [
        {"date": "2023-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2023-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "20.00", "invoice_ids": [str(inv.id)]},
    ]


@freeze_time("2025-01-01")
def test_get_overdue_balance_filter_customer(api_client, user, account):
    past_due = date(2024, 6, 10)
    customer1 = CustomerFactory(account=account)
    customer2 = CustomerFactory(account=account)
    inv1 = InvoiceFactory(
        account=account,
        customer=customer1,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=past_due,
        total_amount=Decimal("20"),
    )
    InvoiceFactory(
        account=account,
        customer=customer2,
        status=InvoiceStatus.OPEN,
        currency="PLN",
        due_date=past_due,
        total_amount=Decimal("30"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/overdue-balance", {"customer_id": str(customer1.id)})

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "20.00", "invoice_ids": [str(inv1.id)]},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_ids": []},
    ]


def test_get_overdue_balance_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/analytics/overdue-balance")

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


def test_get_overdue_balance_requires_authentication(api_client):
    response = api_client.get("/api/v1/analytics/overdue-balance")

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


def test_get_overdue_balance_rejects_foreign_account(api_client, user, account):
    InvoiceFactory(
        status=InvoiceStatus.OPEN,
        due_date=date(2024, 12, 1),
        total_amount=Decimal("25"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/overdue-balance")

    assert response.status_code == 200
    assert all(item["invoice_ids"] == [] for item in response.data)
    assert all(Decimal(item["total_amount"]) == Decimal("0") for item in response.data)
