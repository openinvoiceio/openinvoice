from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from apps.invoices.choices import InvoiceStatus
from tests.factories import CustomerFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-01-01")
def test_get_gross_revenue(api_client, user, account):
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 1, 5),
        total_amount=Decimal("100"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="USD",
        issue_date=date(2024, 1, 20),
        total_amount=Decimal("50"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue")

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "100.00", "invoice_count": 1},
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
    ]


@freeze_time("2025-01-01")
def test_get_gross_revenue_filter_date_after(api_client, user, account):
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 1, 1),
        total_amount=Decimal("10"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("20"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue", {"date_after": "2024-02-01"})

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "20.00", "invoice_count": 1},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
    ]


@freeze_time("2025-01-01")
def test_get_gross_revenue_filter_date_before(api_client, user, account):
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 1, 1),
        total_amount=Decimal("10"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("20"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue", {"date_before": "2024-01-31"})

    assert response.status_code == 200
    assert response.data == [
        {"date": "2023-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-02-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2023-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "10.00", "invoice_count": 1},
    ]


@freeze_time("2025-01-01")
def test_get_gross_revenue_filter_currency(api_client, user, account):
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="USD",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("20"),
    )
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.PAID,
        currency="EUR",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("30"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue", {"currency": "EUR"})

    assert response.status_code == 200
    assert all(item["currency"] == "EUR" for item in response.data)


@freeze_time("2025-01-01")
def test_get_gross_revenue_filter_customer(api_client, user, account):
    customer1 = CustomerFactory(account=account)
    customer2 = CustomerFactory(account=account)
    InvoiceFactory(
        account=account,
        customer=customer1,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("20"),
    )
    InvoiceFactory(
        account=account,
        customer=customer2,
        status=InvoiceStatus.PAID,
        currency="PLN",
        issue_date=date(2024, 2, 1),
        total_amount=Decimal("30"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue", {"customer_id": str(customer1.id)})

    assert response.status_code == 200
    assert response.data == [
        {"date": "2024-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-02-01", "currency": "PLN", "total_amount": "20.00", "invoice_count": 1},
        {"date": "2024-03-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-04-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-05-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-06-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-07-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-08-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-09-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-10-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-11-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2024-12-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
        {"date": "2025-01-01", "currency": "PLN", "total_amount": "0.00", "invoice_count": 0},
    ]


def test_get_gross_revenue_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/analytics/gross-revenue")

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


def test_get_gross_revenue_requires_authentication(api_client):
    response = api_client.get("/api/v1/analytics/gross-revenue")

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


def test_get_gross_revenue_rejects_foreign_account(api_client, user, account):
    InvoiceFactory(status=InvoiceStatus.PAID)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/analytics/gross-revenue")

    assert response.status_code == 200
    assert all(Decimal(item["total_amount"]) == Decimal("0") for item in response.data)
    assert all(item["invoice_count"] == 0 for item in response.data)
